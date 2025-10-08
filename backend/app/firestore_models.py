"""
Helper classes para trabajar con Firestore.
Emulan el comportamiento de SQLAlchemy models pero para Firestore.
"""
from datetime import datetime
from typing import Optional, List, Dict
from .models import CategoryEnum, ModeEnum, StatusEnum
from . import schemas


class FirestoreUser:
    """Helper para User en Firestore"""
    
    @staticmethod
    def to_dict(username: str, email: str, hashed_password: str, is_active: bool = True) -> Dict:
        """Convierte datos de usuario a dict para Firestore"""
        return {
            "username": username,
            "email": email,
            "hashed_password": hashed_password,
            "is_active": is_active,
            "created_at": datetime.utcnow()
        }
    
    @staticmethod
    def to_schema(doc_data: Dict) -> schemas.User:
        """Convierte documento Firestore a schema Pydantic"""
        return schemas.User(
            id=int(doc_data["id"]) if isinstance(doc_data["id"], str) and doc_data["id"].isdigit() else hash(doc_data["id"]) % 1000000,
            username=doc_data["username"],
            email=doc_data["email"],
            is_active=doc_data.get("is_active", True),
            created_at=doc_data.get("created_at", datetime.utcnow())
        )


class FirestoreArticle:
    """Helper para Article en Firestore"""
    
    @staticmethod
    def to_dict(sap_article: str, part_number: str, description: str, category: CategoryEnum) -> Dict:
        """Convierte artículo a dict para Firestore"""
        return {
            "sap_article": sap_article,
            "part_number": part_number,
            "description": description,
            "category": category.value if isinstance(category, CategoryEnum) else category,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    
    @staticmethod
    def to_schema(doc_data: Dict) -> schemas.Article:
        """Convierte documento Firestore a schema Pydantic"""
        return schemas.Article(
            id=int(doc_data["id"]) if isinstance(doc_data["id"], str) and doc_data["id"].isdigit() else hash(doc_data["id"]) % 1000000,
            sap_article=doc_data["sap_article"],
            part_number=doc_data["part_number"],
            description=doc_data["description"],
            category=doc_data["category"],
            created_at=doc_data.get("created_at", datetime.utcnow()),
            updated_at=doc_data.get("updated_at", datetime.utcnow())
        )


class FirestoreBOM:
    """Helper para BOM en Firestore"""
    
    @staticmethod
    def to_dict(name: str, category: CategoryEnum, uploaded_by: str, is_active: bool = True) -> Dict:
        """Convierte BOM a dict para Firestore"""
        return {
            "name": name,
            "category": category.value if isinstance(category, CategoryEnum) else category,
            "uploaded_by": uploaded_by,
            "uploaded_at": datetime.utcnow(),
            "is_active": is_active
        }
    
    @staticmethod
    def to_schema(doc_data: Dict, items: List[Dict] = None) -> schemas.BOM:
        """Convierte documento Firestore a schema Pydantic"""
        bom_items = []
        if items:
            for item in items:
                bom_items.append(schemas.BOMItem(
                    id=int(item["id"]) if isinstance(item["id"], str) and item["id"].isdigit() else hash(item["id"]) % 1000000,
                    bom_id=int(doc_data["id"]) if isinstance(doc_data["id"], str) and doc_data["id"].isdigit() else hash(doc_data["id"]) % 1000000,
                    sap_article=item["sap_article"],
                    part_number=item["part_number"],
                    description=item["description"],
                    quantity=item["quantity"]
                ))
        
        return schemas.BOM(
            id=int(doc_data["id"]) if isinstance(doc_data["id"], str) and doc_data["id"].isdigit() else hash(doc_data["id"]) % 1000000,
            name=doc_data["name"],
            category=doc_data["category"],
            uploaded_by=int(doc_data["uploaded_by"]) if isinstance(doc_data["uploaded_by"], str) and doc_data["uploaded_by"].isdigit() else 1,
            uploaded_at=doc_data.get("uploaded_at", datetime.utcnow()),
            is_active=doc_data.get("is_active", True),
            items=bom_items
        )


class FirestoreBOMItem:
    """Helper para BOMItem en Firestore (subcollection)"""
    
    @staticmethod
    def to_dict(sap_article: str, part_number: str, description: str, quantity: float) -> Dict:
        """Convierte BOM item a dict para Firestore"""
        return {
            "sap_article": sap_article,
            "part_number": part_number,
            "description": description,
            "quantity": quantity
        }


class FirestoreScanSession:
    """Helper para ScanSession en Firestore"""
    
    @staticmethod
    def to_dict(user_id: str, mode: ModeEnum, category: Optional[CategoryEnum] = None, 
                bom_id: Optional[str] = None, is_active: bool = True) -> Dict:
        """Convierte sesión a dict para Firestore"""
        return {
            "user_id": user_id,
            "mode": mode.value if isinstance(mode, ModeEnum) else mode,
            "category": category.value if category and isinstance(category, CategoryEnum) else category,
            "bom_id": bom_id,
            "started_at": datetime.utcnow(),
            "ended_at": None,
            "is_active": is_active
        }
    
    @staticmethod
    def to_schema(doc_data: Dict, bom: Optional[schemas.BOM] = None, records: List[Dict] = None) -> schemas.ScanSession:
        """Convierte documento Firestore a schema Pydantic"""
        session_records = []
        if records:
            for record in records:
                session_records.append(schemas.ScanRecord(
                    id=int(record["id"]) if isinstance(record["id"], str) and record["id"].isdigit() else hash(record["id"]) % 1000000,
                    session_id=int(doc_data["id"]) if isinstance(doc_data["id"], str) and doc_data["id"].isdigit() else hash(doc_data["id"]) % 1000000,
                    sap_article=record["sap_article"],
                    part_number=record.get("part_number"),
                    description=record.get("description"),
                    po_number=record.get("po_number"),
                    quantity=record.get("quantity", 1.0),
                    scanned_at=record.get("scanned_at", datetime.utcnow()),
                    manual_entry=record.get("manual_entry", False),
                    detected_category=record.get("detected_category"),
                    expected_quantity=record.get("expected_quantity"),
                    status=record.get("status")
                ))
        
        return schemas.ScanSession(
            id=int(doc_data["id"]) if isinstance(doc_data["id"], str) and doc_data["id"].isdigit() else hash(doc_data["id"]) % 1000000,
            user_id=int(doc_data["user_id"]) if isinstance(doc_data["user_id"], str) and doc_data["user_id"].isdigit() else 1,
            mode=doc_data["mode"],
            category=doc_data.get("category"),
            bom_id=int(doc_data["bom_id"]) if doc_data.get("bom_id") and isinstance(doc_data["bom_id"], str) and doc_data["bom_id"].isdigit() else doc_data.get("bom_id"),
            started_at=doc_data.get("started_at", datetime.utcnow()),
            ended_at=doc_data.get("ended_at"),
            is_active=doc_data.get("is_active", True),
            bom=bom,
            records=session_records
        )


class FirestoreScanRecord:
    """Helper para ScanRecord en Firestore (subcollection)"""
    
    @staticmethod
    def to_dict(sap_article: str, part_number: Optional[str] = None, description: Optional[str] = None,
                po_number: Optional[str] = None, quantity: float = 1.0, manual_entry: bool = False,
                detected_category: Optional[CategoryEnum] = None, expected_quantity: Optional[float] = None,
                status: Optional[StatusEnum] = None) -> Dict:
        """Convierte scan record a dict para Firestore"""
        return {
            "sap_article": sap_article,
            "part_number": part_number,
            "description": description,
            "po_number": po_number,
            "quantity": quantity,
            "scanned_at": datetime.utcnow(),
            "manual_entry": manual_entry,
            "detected_category": detected_category.value if detected_category and isinstance(detected_category, CategoryEnum) else detected_category,
            "expected_quantity": expected_quantity,
            "status": status.value if status and isinstance(status, StatusEnum) else status
        }
