import os
import shutil
import tempfile
import urllib.parse
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field

from adapters.tts_audio import GoogleTTSAudioAdapter
from bridge.desktop_facade import ALLOWED_EXTENSIONS, DesktopFacade
from core.logger import get_logger

logger = get_logger("api_server")


MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_TEXT_LENGTH = 5000


class TranslateRequest(BaseModel):
    text_zh: str = Field(..., alias="textZh", max_length=MAX_TEXT_LENGTH)

    model_config = ConfigDict(populate_by_name=True)


class PinyinResponse(BaseModel):
    text: str
    pinyin: str


def create_app(facade: DesktopFacade | None = None) -> FastAPI:
    """Fábrica de la aplicación FastAPI que permite inyectar una fachada o instanciar la real."""
    active_facade: DesktopFacade | None = facade

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        nonlocal active_facade
        if active_facade is None:
            logger.info("Inicializando DesktopFacade real para Moon Shang API...")
            try:
                from main import create_facade

                active_facade = create_facade()
                logger.info("DesktopFacade inicializado con éxito en FastAPI.")
            except Exception:
                logger.exception("Error al inicializar DesktopFacade en el servidor API")
        yield

    app = FastAPI(
        title="Moon Shang Mobile & Web API",
        version="0.1.0",
        description="API HTTP para el procesamiento de documentos chinos, OCR, Pinyin y traducción.",
        lifespan=lifespan,
    )

    # Configuración de CORS permitiendo orígenes móviles y locales
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def get_facade() -> DesktopFacade:
        nonlocal active_facade
        if active_facade is None:
            from main import create_facade

            active_facade = create_facade()
        return active_facade

    @app.get("/health")
    def health_check():
        """Comprueba el estado del servidor y la conectividad para clientes móviles."""
        return {
            "status": "ok",
            "healthy": True,
            "service": "moon_shang_api",
            "version": "0.1.0",
            "mode": "online",
        }

    @app.post("/api/translate")
    def translate_token(request: TranslateRequest):
        """Traduce un carácter o término chino al español con Pinyin."""
        text = request.text_zh.strip()
        if not text:
            raise HTTPException(status_code=400, detail="El campo 'textZh' no puede estar vacío.")

        f = get_facade()
        try:
            return f.translate_token(text)
        except Exception as e:
            logger.exception("Error en /api/translate para: %r", text)
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.get("/api/pinyin", response_model=PinyinResponse)
    def get_pinyin(text: str):
        """Devuelve la transcripción fonética Pinyin con tonos para el texto indicado."""
        cleaned = text.strip()
        if not cleaned:
            raise HTTPException(status_code=400, detail="El parámetro 'text' no puede estar vacío.")
        if len(cleaned) > MAX_TEXT_LENGTH:
            raise HTTPException(
                status_code=400, detail=f"Longitud de texto supera el límite permitido ({MAX_TEXT_LENGTH} caracteres)."
            )

        f = get_facade()
        try:
            pinyin_str = f.get_pinyin(cleaned)
            return PinyinResponse(text=cleaned, pinyin=pinyin_str)
        except Exception as e:
            logger.exception("Error en /api/pinyin para: %r", cleaned)
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.get("/api/audio")
    def get_audio(text: str):
        """Descarga o recupera el archivo MP3 de pronunciación del texto solicitado."""
        cleaned = text.strip()
        if not cleaned:
            raise HTTPException(status_code=400, detail="El parámetro 'text' no puede estar vacío.")
        if len(cleaned) > 200:
            raise HTTPException(status_code=400, detail="El parámetro 'text' para audio no debe exceder 200 caracteres.")

        try:
            tts = GoogleTTSAudioAdapter()
            audio_path = tts.download_audio(cleaned)
            if audio_path and os.path.exists(audio_path):
                # Verificación estricta de confinamiento de ruta (prevención de Path Traversal)
                canon_path = os.path.realpath(os.path.abspath(audio_path))
                canon_dir = os.path.realpath(os.path.abspath(tts.cache_dir))
                if os.path.commonpath([canon_path, canon_dir]) != canon_dir:
                    logger.error("Detección de path traversal en ruta de audio: %s", audio_path)
                    raise HTTPException(status_code=403, detail="Acceso denegado a la ruta del archivo de audio.")

                safe_filename = f"{urllib.parse.quote(cleaned[:30])}.mp3"
                return FileResponse(
                    canon_path,
                    media_type="audio/mpeg",
                    filename=safe_filename,
                )
            raise HTTPException(
                status_code=500, detail="No se pudo generar el audio de pronunciación."
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Error al servir audio de pronunciación para '%s'", cleaned)
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.post("/api/process-page")
    def process_page(
        file: Annotated[UploadFile, File(...)],
        page_number: Annotated[int, Form()] = 1,
    ):
        """Recibe una imagen o PDF vía multipart, ejecuta OCR y retorna los tokens detectados."""
        if not file.filename:
            raise HTTPException(status_code=400, detail="Nombre de archivo inválido o vacío.")

        # Sanitizar nombre de archivo contra path traversal
        clean_filename = os.path.basename(file.filename.strip())
        _, ext = os.path.splitext(clean_filename.lower())
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Formato no permitido: '{ext}'. Formatos soportados: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            )

        if page_number < 1:
            raise HTTPException(status_code=400, detail="El número de página debe ser mayor o igual a 1.")

        # Guardar en archivo temporal seguro con límite de tamaño para evitar DoS
        total_size = 0
        chunk_size = 1024 * 1024  # 1 MB por bloque
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            temp_path = tmp.name
            try:
                while True:
                    chunk = file.file.read(chunk_size)
                    if not chunk:
                        break
                    total_size += len(chunk)
                    if total_size > MAX_UPLOAD_SIZE:
                        raise HTTPException(
                            status_code=413,
                            detail=f"El archivo excede el tamaño máximo permitido de {MAX_UPLOAD_SIZE // (1024 * 1024)} MB.",
                        )
                    tmp.write(chunk)
            except Exception:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass
                raise

        try:
            f = get_facade()
            return f.process_page(temp_path, page_number)
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Error procesando página %d de archivo subido", page_number)
            raise HTTPException(status_code=500, detail=str(e)) from e
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError as err:
                    logger.debug("No se pudo eliminar archivo temporal %s: %s", temp_path, err)

    return app


# Instancia por defecto para ejecutarse directamente con uvicorn src.api_server:app
app = create_app()
