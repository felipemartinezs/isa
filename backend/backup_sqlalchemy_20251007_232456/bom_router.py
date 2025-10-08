from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, auth
from ..database import get_db
from ..excel_handler import parse_bom_excel

router = APIRouter(prefix="/boms", tags=["bom"])


@router.post("/upload", response_model=schemas.BOM)
async def upload_bom(
    name: str = Form(...),
    category: str = Form(...),
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Upload BOM from Excel file"""
    if not file.filename.endswith(('.xlsx', '.xls', '.xlsm')):
                        raise HTTPException(status_code=400, detail="File must be an Excel file (.xlsx, .xls, or .xlsm)")
    
    # Validate category
    try:
        category_enum = models.CategoryEnum(category)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
    
    try:
        content = await file.read()
        # Pass category to filter BOM items
        bom_items_data = parse_bom_excel(content, target_category=category)
        
        if len(bom_items_data) == 0:
            raise ValueError(f"No items found for category '{category}'. The Excel may not have a category column, or all items were filtered out.")
        
        # Create BOM
        db_bom = models.BOM(
            name=name,
            category=category_enum,
            uploaded_by=current_user.id
        )
        db.add(db_bom)
        db.flush()
        
        # Create BOM items
        for item_data in bom_items_data:
            db_item = models.BOMItem(
                bom_id=db_bom.id,
                **item_data
            )
            db.add(db_item)
        
        db.commit()
        db.refresh(db_bom)
        
        # Explicitly load items relationship
        db.refresh(db_bom)
        items_count = len(db_bom.items)
        print(f"✅ BOM created with {items_count} items: '{name}'")
        
        return db_bom
    
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.get("/", response_model=List[schemas.BOM])
def get_boms(
    category: str = None,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get all BOMs with optional category filter"""
    from sqlalchemy.orm import joinedload
    
    query = db.query(models.BOM).options(joinedload(models.BOM.items)).filter(models.BOM.is_active == True)
    
    if category:
        try:
            category_enum = models.CategoryEnum(category)
            query = query.filter(models.BOM.category == category_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
    
    boms = query.order_by(models.BOM.uploaded_at.desc()).all()

    # Agregar items_count manualmente
    response = []
    for bom in boms:
        bom_data = schemas.BOM.from_orm(bom)
        # Agregar campo calculado
        bom_dict = bom_data.dict()
        bom_dict['items_count'] = len(bom.items)
        response.append(bom_dict)
        print(f"BOM '{bom.name}': {bom_dict['items_count']} items")

    return response


@router.get("/{bom_id}", response_model=schemas.BOM)
def get_bom(
    bom_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get BOM by ID"""
    bom = db.query(models.BOM).filter(models.BOM.id == bom_id).first()
    
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")
    
    return bom


@router.delete("/{bom_id}")
def delete_bom(
    bom_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete BOM (soft delete)"""
    bom = db.query(models.BOM).filter(models.BOM.id == bom_id).first()
    
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")
    
    bom.is_active = False
    db.commit()
    
    return {"message": "BOM deleted successfully"}


@router.get("/{bom_id}/items", response_model=List[schemas.BOMItem])
def get_bom_items(
    bom_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get all items for a BOM"""
    bom = db.query(models.BOM).filter(models.BOM.id == bom_id).first()
    
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")
    
    return bom.items
