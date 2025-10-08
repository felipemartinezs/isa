"""
Enums y constantes usados en el proyecto
Las clases de SQLAlchemy fueron migradas a Firestore
"""
from enum import Enum

class CategoryEnum(str, Enum):
    PCB = "PCB"
    ELECTRONIC = "ELECTRONIC"
    MECHANICAL = "MECHANICAL"

class ModeEnum(str, Enum):
    INVENTORY = "INVENTORY"
    BOM = "BOM"

class StatusEnum(str, Enum):
    OK = "OK"
    MISSING = "MISSING"
    EXTRA = "EXTRA"
    QUANTITY_MISMATCH = "QUANTITY_MISMATCH"
