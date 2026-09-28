"""Document Converter: convert documents, spreadsheets, slides and markup files."""

__version__ = "1.0.0"
APP_NAME = "Document Converter"

from .converter import Converter  # noqa: E402
from .engines import ConversionError  # noqa: E402
from .formats import FORMATS, detect  # noqa: E402

__all__ = ["Converter", "ConversionError", "FORMATS", "detect", "__version__", "APP_NAME"]
