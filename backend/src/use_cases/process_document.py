import base64
import os

import cv2
import numpy as np

from domain.entities import DocumentData, PageData
from domain.ports import IOCREngine, IPdfExtractor
from use_cases.translate_token import TranslateTokenUseCase


class ProcessDocumentUseCase:
    """Caso de uso principal para procesar documentos PDF o imágenes."""

    def __init__(
        self,
        pdf_extractor: IPdfExtractor,
        ocr_engine: IOCREngine,
        translate_use_case: TranslateTokenUseCase,
    ):
        self.pdf_extractor = pdf_extractor
        self.ocr_engine = ocr_engine
        self.translate_use_case = translate_use_case

    def _is_pdf(self, source: str | bytes, filename: str) -> bool:
        return filename.lower().endswith(".pdf") or (
            isinstance(source, bytes) and source.startswith(b"%PDF")
        )

    def get_document_info(self, source: str | bytes, filename: str) -> DocumentData:
        is_pdf = self._is_pdf(source, filename)
        file_type = "pdf" if is_pdf else "image"
        total_pages = self.pdf_extractor.get_page_count(source) if is_pdf else 1

        return DocumentData(
            id=os.path.basename(filename),
            filename=source if isinstance(source, str) else filename,
            fileType=file_type,
            totalPages=total_pages,
            currentPage=1,
            pages=[],
        )

    def process_page(
        self,
        source: str | bytes,
        filename: str,
        page_number: int = 1,
        auto_translate: bool = True,
        dpi: int = 150,
    ) -> PageData:
        is_pdf = self._is_pdf(source, filename)

        if is_pdf:
            image_bytes, width, height = self.pdf_extractor.extract_page_as_image(
                source, page_number=page_number, dpi=dpi
            )
        else:
            if isinstance(source, bytes):
                image_bytes = source
            else:
                with open(source, "rb") as f:
                    image_bytes = f.read()

            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("No se pudo cargar la imagen provista.")
            height, width = img.shape[:2]

        # 1. Ejecutar OCR para detectar caracteres chinos y coordenadas
        tokens = self.ocr_engine.detect_text(image_bytes)

        # 2. Si auto_translate está activo, traducir cada token
        if auto_translate:
            for token in tokens:
                if not token.translation_es and token.text_zh:
                    trans_result = self.translate_use_case.execute(token.text_zh)
                    token.translation_es = trans_result.translation_es
                    if not token.pinyin:
                        token.pinyin = trans_result.pinyin

        # 3. Codificar la imagen a Data URI en Base64 para visualización en el frontend
        base64_str = base64.b64encode(image_bytes).decode("utf-8")
        image_url = f"data:image/png;base64,{base64_str}"

        return PageData(
            pageNumber=page_number,
            width=width,
            height=height,
            imageUrl=image_url,
            tokens=tokens,
        )
