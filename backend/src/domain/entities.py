from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class BoundingBox(BaseModel):
    """Coordenadas de una caja delimitadora en la resolución original de la imagen."""
    x1: float = Field(..., description="Coordenada X superior izquierda")
    y1: float = Field(..., description="Coordenada Y superior izquierda")
    x2: float = Field(..., description="Coordenada X inferior derecha")
    y2: float = Field(..., description="Coordenada Y inferior derecha")

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    def to_rect_dict(self) -> dict:
        return {
            "x": self.x1,
            "y": self.y1,
            "width": self.width,
            "height": self.height,
        }


class DetectedToken(BaseModel):
    """Representa un token o bloque de texto chino detectado."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    text_zh: str = Field(..., alias="textZh")
    pinyin: str
    translation_es: str = Field(default="", alias="translationEs")
    box: BoundingBox
    confidence: float = Field(default=1.0)


class PageData(BaseModel):
    """Datos de una página analizada."""
    model_config = ConfigDict(populate_by_name=True)

    page_number: int = Field(..., alias="pageNumber")
    width: int
    height: int
    image_url: str = Field(default="", alias="imageUrl")
    tokens: list[DetectedToken] = Field(default_factory=list)


class FileType(str, Enum):
    IMAGE = "image"
    PDF = "pdf"


class DocumentData(BaseModel):
    """Representa un documento procesado completo."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    filename: str
    file_type: Literal["image", "pdf"] = Field(..., alias="fileType")
    total_pages: int = Field(default=1, alias="totalPages")
    current_page: int = Field(default=1, alias="currentPage")
    pages: list[PageData] = Field(default_factory=list)


class TranslationResult(BaseModel):
    """Resultado de la traducción de un término o frase."""
    model_config = ConfigDict(populate_by_name=True)

    text_zh: str = Field(..., alias="textZh")
    pinyin: str
    translation_es: str = Field(..., alias="translationEs")
    from_cache: bool = Field(default=False, alias="fromCache")
