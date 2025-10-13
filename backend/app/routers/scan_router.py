from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict
from datetime import datetime
from .. import models, schemas, auth
from ..database import get_db
from ..sse import sse_manager
import json

router = APIRouter(prefix="/scan", tags=["scanning"])


@router.post("/sessions", response_model=schemas.ScanSession)
async def create_session(
    session_data: schemas.ScanSessionCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new scan session"""
    # ⭐ NUEVA VALIDACIÓN
    if session_data.mode == models.ModeEnum.BOM:
        if not session_data.category:
            raise HTTPException(status_code=400, detail="Category required for BOM mode")
        if not session_data.bom_id:
            raise HTTPException(status_code=400, detail="BOM ID required for BOM mode")
        
        bom = db.query(models.BOM).filter(models.BOM.id == session_data.bom_id).first()
        if not bom:
            raise HTTPException(status_code=404, detail="BOM not found")
        
        if bom.category != session_data.category:
            raise HTTPException(status_code=400, detail="BOM category must match session category")
    elif session_data.mode == models.ModeEnum.INVENTORY:
        # INVENTORY mode no requiere category
        session_data.category = None
    
    # Create session
    db_session = models.ScanSession(
        user_id=current_user.id,
        mode=session_data.mode,
        category=session_data.category,  # Puede ser None para INVENTORY
        bom_id=session_data.bom_id
    )
    
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    return db_session


@router.get("/sessions", response_model=List[schemas.ScanSession])
def get_sessions(
    active_only: bool = False,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get all scan sessions for current user"""
    from sqlalchemy.orm import joinedload
    
    query = db.query(models.ScanSession).options(
        joinedload(models.ScanSession.bom).joinedload(models.BOM.items)
    ).filter(
        models.ScanSession.user_id == current_user.id
    )
    
    if active_only:
        query = query.filter(models.ScanSession.is_active == True)
    
    sessions = query.order_by(models.ScanSession.started_at.desc()).all()
    
    # Enrich sessions with BOM info
    response = []
    for session in sessions:
        # Build response dict manually to include computed fields
        bom_name = None
        bom_items_count = None
        scanned_items_count = len(session.records)  # ⭐ AGREGAR ESTA LÍNEA

        if session.bom:
            bom_name = session.bom.name
            bom_items_count = len(session.bom.items)

        # Use model_validate for Pydantic V2
        session_response = schemas.ScanSession(
            id=session.id,
            user_id=session.user_id,
            mode=session.mode,
            category=session.category,
            bom_id=session.bom_id,
            started_at=session.started_at,
            ended_at=session.ended_at,
            is_active=session.is_active,
            bom_name=bom_name,
            bom_items_count=bom_items_count,
            scanned_items_count=scanned_items_count  # ⭐ AGREGAR ESTA LÍNEA
        )
        response.append(session_response)
    
    return response

@router.get("/sessions/{session_id}", response_model=schemas.ScanSession)
def get_session(
    session_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get session by ID"""
    session = db.query(models.ScanSession).filter(
        models.ScanSession.id == session_id,
        models.ScanSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session


@router.post("/sessions/{session_id}/end")
async def end_session(
    session_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """End a scan session"""
    session = db.query(models.ScanSession).filter(
        models.ScanSession.id == session_id,
        models.ScanSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.is_active = False
    session.ended_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Session ended successfully"}


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a scan session and all its records"""
    session = db.query(models.ScanSession).filter(
        models.ScanSession.id == session_id,
        models.ScanSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Delete all records first (cascade should handle this, but being explicit)
    db.query(models.ScanRecord).filter(
        models.ScanRecord.session_id == session_id
    ).delete()
    
    # Delete the session
    db.delete(session)
    db.commit()
    
    # Broadcast SSE event
    event_data = {
        "event": "session_deleted",
        "data": json.dumps({
            "type": "session_deleted",
            "session_id": session_id
        })
    }
    
    await sse_manager.broadcast_all(event_data)
    
    return {"message": "Session deleted successfully"}


@router.post("/records", response_model=schemas.ScanRecord)
async def create_scan_record(
    record_data: schemas.ScanRecordCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new scan record"""
    print(f"\n{'='*60}")
    print(f"📥 Received scan: {record_data.sap_article} x{record_data.quantity}")
    print(f"   Session: {record_data.session_id}, User: {current_user.username}")
    print(f"{'='*60}\n")
    
    # Validate session
    session = db.query(models.ScanSession).filter(
        models.ScanSession.id == record_data.session_id,
        models.ScanSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.is_active:
        raise HTTPException(status_code=400, detail="Session is not active")
    
    # Look up article in database
    article = db.query(models.Article).filter(
        models.Article.sap_article == record_data.sap_article
    ).first()

    # Auto-detect category from article database
    detected_cat = None
    if article:
        detected_cat = article.category
    elif record_data.detected_category:
        # Use manually provided category (for articles not in DB)
        detected_cat = record_data.detected_category
    else:
        # Fallback to session category
        detected_cat = session.category

    print(f"   🏷️  Category detected: {detected_cat.value if detected_cat else 'None'}")

    # Create scan record
    db_record = models.ScanRecord(
        session_id=record_data.session_id,
        sap_article=record_data.sap_article,
        part_number=article.part_number if article else None,
        description=article.description if article else None,
        detected_category=detected_cat,  # ⭐ NUEVO
        po_number=record_data.po_number,
        quantity=record_data.quantity,
        manual_entry=record_data.manual_entry
    )
    
    # If in BOM mode, calculate comparison
    if session.mode == models.ModeEnum.BOM and session.bom_id:
        # Get BOM item
        bom_item = db.query(models.BOMItem).filter(
            models.BOMItem.bom_id == session.bom_id,
            models.BOMItem.sap_article == record_data.sap_article
        ).first()
        
        if bom_item:
            db_record.expected_quantity = bom_item.quantity
            
            # Count total scanned quantity for this article in this session
            total_scanned = db.query(func.sum(models.ScanRecord.quantity)).filter(
                models.ScanRecord.session_id == session.id,
                models.ScanRecord.sap_article == record_data.sap_article
            ).scalar() or 0.0
            
            total_scanned += record_data.quantity
            
            # Determine status
            if total_scanned == bom_item.quantity:
                db_record.status = models.StatusEnum.MATCH
            elif total_scanned > bom_item.quantity:
                db_record.status = models.StatusEnum.OVER
            else:
                db_record.status = models.StatusEnum.UNDER
        else:
            # Article not in BOM
            db_record.status = models.StatusEnum.OVER
    
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    
    # Broadcast SSE event
    event_data = {
        "event": "scan",
        "data": json.dumps({
            "type": "scan",
            "session_id": session.id,
            "record": {
                "id": db_record.id,
                "sap_article": db_record.sap_article,
                "part_number": db_record.part_number,
                "description": db_record.description,
                "po_number": db_record.po_number,
                "quantity": db_record.quantity,
                "scanned_at": db_record.scanned_at.isoformat(),
                "manual_entry": db_record.manual_entry,
                "expected_quantity": db_record.expected_quantity,
                "status": db_record.status.value if db_record.status else None,
                "detected_category": db_record.detected_category.value if db_record.detected_category else None
            }
        })
    }
    
    await sse_manager.broadcast(session.id, event_data)
    await sse_manager.broadcast_all(event_data)  # Also broadcast to panel
    
    return db_record


@router.get("/sessions/{session_id}/records", response_model=List[schemas.ScanRecord])
def get_session_records(
    session_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get all scan records for a session"""
    session = db.query(models.ScanSession).filter(
        models.ScanSession.id == session_id,
        models.ScanSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session.records


@router.get("/sessions/{session_id}/summary")
def get_session_summary(
    session_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get summary of scan session with BOM comparison - showing individual records"""
    session = db.query(models.ScanSession).filter(
        models.ScanSession.id == session_id,
        models.ScanSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get individual scan records instead of aggregated
    scan_records = db.query(models.ScanRecord).filter(
        models.ScanRecord.session_id == session_id
    ).order_by(models.ScanRecord.scanned_at.desc()).all()
    
    summary = []
    match_count = 0
    over_count = 0
    under_count = 0
    
    # Show individual records with their IDs for editing/deleting
    for record in scan_records:
        expected_qty = record.expected_quantity if record.expected_quantity else None
        scanned_qty = record.quantity
        
        # Determine status
        if record.status:
            status = record.status.value
        else:
            status = "COUNTED"
        
        if status == "MATCH":
            match_count += 1
        elif status == "OVER":
            over_count += 1
        elif status == "UNDER":
            under_count += 1
        
        item_data = {
            "record_id": record.id,
            "sap_article": record.sap_article,
            "part_number": record.part_number,
            "description": record.description,
            "scanned_quantity": scanned_qty,
            "status": status,
            "detected_category": record.detected_category.value if record.detected_category else None
        }
        
        if expected_qty is not None:
            item_data["expected_quantity"] = expected_qty
            item_data["difference"] = scanned_qty - expected_qty
        
        summary.append(item_data)
    
    return {
        "session": session,
        "items": summary,
        "total_items": len(summary),
        "match_count": sum(1 for item in summary if item.get("status") == "MATCH"),
        "over_count": sum(1 for item in summary if item.get("status") == "OVER"),
        "under_count": sum(1 for item in summary if item.get("status") == "UNDER")
    }


@router.delete("/records/{record_id}")
async def delete_scan_record(
    record_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a scan record (admin only or owner)"""
    # Get the record
    record = db.query(models.ScanRecord).filter(
        models.ScanRecord.id == record_id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    # Check permission - must be owner of session or admin
    session = db.query(models.ScanSession).filter(
        models.ScanSession.id == record.session_id
    ).first()
    
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this record")
    
    db.delete(record)
    db.commit()
    
    # Broadcast SSE event
    event_data = {
        "event": "record_deleted",
        "data": json.dumps({
            "type": "record_deleted",
            "session_id": session.id,
            "record_id": record_id
        })
    }
    
    await sse_manager.broadcast(session.id, event_data)
    await sse_manager.broadcast_all(event_data)
    
    return {"message": "Record deleted successfully"}


@router.put("/records/{record_id}", response_model=schemas.ScanRecord)
async def update_scan_record(
    record_id: int,
    quantity: float,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Update scan record quantity (admin only or owner)"""
    # Get the record
    record = db.query(models.ScanRecord).filter(
        models.ScanRecord.id == record_id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    # Check permission
    session = db.query(models.ScanSession).filter(
        models.ScanSession.id == record.session_id
    ).first()
    
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this record")
    
    # Update quantity
    record.quantity = quantity
    
    # Recalculate status if in BOM mode
    if session.mode == models.ModeEnum.BOM and session.bom_id:
        bom_item = db.query(models.BOMItem).filter(
            models.BOMItem.bom_id == session.bom_id,
            models.BOMItem.sap_article == record.sap_article
        ).first()
        
        if bom_item:
            # Count total scanned quantity for this article in this session
            total_scanned = db.query(func.sum(models.ScanRecord.quantity)).filter(
                models.ScanRecord.session_id == session.id,
                models.ScanRecord.sap_article == record.sap_article
            ).scalar() or 0.0
            
            # Determine status
            if total_scanned == bom_item.quantity:
                record.status = models.StatusEnum.MATCH
            elif total_scanned > bom_item.quantity:
                record.status = models.StatusEnum.OVER
            else:
                record.status = models.StatusEnum.UNDER
    
    db.commit()
    db.refresh(record)
    
    # Broadcast SSE event
    event_data = {
        "event": "record_updated",
        "data": json.dumps({
            "type": "record_updated",
            "session_id": session.id,
            "record": {
                "id": record.id,
                "sap_article": record.sap_article,
                "quantity": record.quantity,
                "status": record.status.value if record.status else None
            }
        })
    }
    
    await sse_manager.broadcast(session.id, event_data)
    await sse_manager.broadcast_all(event_data)
    
    return record


@router.get("/overview")
def get_inventory_overview(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get inventory overview for all categories + INVENTORY mode sessions
    """
    from sqlalchemy.orm import joinedload
    
    overview = []
    
    # ⭐ CATEGORÍAS TRADICIONALES (CCTV, CX, FIRE)
    for category in models.CategoryEnum:
        # Get most recent BOM for this category
        bom = db.query(models.BOM).filter(
            models.BOM.category == category,
            models.BOM.is_active == True
        ).order_by(models.BOM.uploaded_at.desc()).first()
        
        # Get ALL active BOM sessions for this category (not INVENTORY)
        active_sessions = db.query(models.ScanSession).filter(
            models.ScanSession.category == category,
            
            models.ScanSession.is_active == True,
            models.ScanSession.user_id == current_user.id
        ).order_by(models.ScanSession.started_at.desc()).all()
        
        # Get last session
        last_session = db.query(models.ScanSession).filter(
            models.ScanSession.category == category,
            
            models.ScanSession.user_id == current_user.id
        ).order_by(models.ScanSession.started_at.desc()).first()
        
        # Calculate progress for active sessions...
        # [El resto del código de cálculo de progress permanece igual]
        progress = None
        active_sessions_list = []
        
        if active_sessions:
            total_scanned = 0
            total_match = 0
            total_over = 0
            total_under = 0
            expected_items = 0
            
            for session in active_sessions:
                session_scanned = db.query(func.count(models.ScanRecord.id)).filter(
                    models.ScanRecord.session_id == session.id
                ).scalar() or 0
                
                session_expected = 0
                if session.bom_id:
                    session_expected = db.query(func.count(models.BOMItem.id)).filter(
                        models.BOMItem.bom_id == session.bom_id
                    ).scalar() or 0
                
                session_match = db.query(func.count(models.ScanRecord.id)).filter(
                    models.ScanRecord.session_id == session.id,
                    models.ScanRecord.status == models.StatusEnum.MATCH
                ).scalar() or 0
                
                session_over = db.query(func.count(models.ScanRecord.id)).filter(
                    models.ScanRecord.session_id == session.id,
                    models.ScanRecord.status == models.StatusEnum.OVER
                ).scalar() or 0
                
                session_under = db.query(func.count(models.ScanRecord.id)).filter(
                    models.ScanRecord.session_id == session.id,
                    models.ScanRecord.status == models.StatusEnum.UNDER
                ).scalar() or 0
                
                total_scanned += session_scanned
                total_match += session_match
                total_over += session_over
                total_under += session_under
                expected_items += session_expected
                
                active_sessions_list.append({
                    "id": session.id,
                    "mode": session.mode.value,
                    "started_at": session.started_at.isoformat(),
                    "bom_name": session.bom.name if session.bom else None,
                    "scanned_items": session_scanned,
                    "expected_items": session_expected,
                    "match_count": session_match,
                    "over_count": session_over,
                    "under_count": session_under
                })
            
            progress = {
                "scanned_items": total_scanned,
                "expected_items": expected_items if expected_items > 0 else None,
                "match_count": total_match,
                "over_count": total_over,
                "under_count": total_under
            }
        
        status = "not_started"
        if active_sessions:
            status = "in_progress"
        elif last_session and not last_session.is_active:
            status = "completed"
        
        category_data = {
            "category": category.value,
            "status": status,
            "bom": {
                "id": bom.id if bom else None,
                "name": bom.name if bom else None,
                "items_count": len(bom.items) if bom else 0,
                "uploaded_at": bom.uploaded_at.isoformat() if bom else None
            } if bom else None,
            "active_sessions": active_sessions_list,
            "last_session": {
                "id": last_session.id,
                "mode": last_session.mode.value,
                "started_at": last_session.started_at.isoformat(),
                "ended_at": last_session.ended_at.isoformat() if last_session.ended_at else None,
                "is_active": last_session.is_active
            } if last_session else None,
            "progress": progress
        }
        
        overview.append(category_data)
    
    # ⭐    # ⭐ NUEVA SECCIÓN: INVENTORY (con indicadores de progreso)
    # First, load all active BOMs for comparison
    active_boms = {}
    for category in models.CategoryEnum:
        bom = db.query(models.BOM).filter(
            models.BOM.category == category,
            models.BOM.is_active == True
        ).order_by(models.BOM.uploaded_at.desc()).first()
        if bom:
            active_boms[category] = bom
    
    inventory_active_sessions = db.query(models.ScanSession).filter(
        models.ScanSession.mode == models.ModeEnum.INVENTORY,
        models.ScanSession.is_active == True,
        models.ScanSession.user_id == current_user.id
    ).order_by(models.ScanSession.started_at.desc()).all()
    
    inventory_last_session = db.query(models.ScanSession).filter(
        models.ScanSession.mode == models.ModeEnum.INVENTORY,
        models.ScanSession.user_id == current_user.id
    ).order_by(models.ScanSession.started_at.desc()).first()
    
    inventory_sessions_list = []
    inventory_status = "not_started"
    
    if inventory_active_sessions:
        inventory_status = "in_progress"
        for session in inventory_active_sessions:
            session_scanned = db.query(func.count(models.ScanRecord.id)).filter(
                models.ScanRecord.session_id == session.id
            ).scalar() or 0
            
            # Calculate match/over/under counts by comparing against BOMs
            # Group records by article and detected_category, sum quantities
            article_totals = db.query(
                models.ScanRecord.sap_article,
                models.ScanRecord.detected_category,
                func.sum(models.ScanRecord.quantity).label('total_qty')
            ).filter(
                models.ScanRecord.session_id == session.id
            ).group_by(
                models.ScanRecord.sap_article,
                models.ScanRecord.detected_category
            ).all()
            
            session_match = 0
            session_over = 0
            session_under = 0
            session_expected = 0
            
            for sap_article, detected_cat, total_qty in article_totals:
                if detected_cat and detected_cat in active_boms:
                    # Find BOM item for this category
                    bom = active_boms[detected_cat]
                    bom_item = db.query(models.BOMItem).filter(
                        models.BOMItem.bom_id == bom.id,
                        models.BOMItem.sap_article == sap_article
                    ).first()
                    
                    if bom_item:
                        session_expected += 1
                        expected_qty = bom_item.quantity
                        if total_qty == expected_qty:
                            session_match += 1
                        elif total_qty > expected_qty:
                            session_over += 1
                        else:
                            session_under += 1
                    else:
                        # Article not in BOM = OVER
                        session_over += 1
                else:
                    # No category detected or no BOM = count as OVER
                    session_over += 1
            
            inventory_sessions_list.append({
                "id": session.id,
                "mode": session.mode.value,
                "started_at": session.started_at.isoformat(),
                "scanned_items": session_scanned,
                "expected_items": session_expected if session_expected > 0 else None,
                "match_count": session_match,
                "over_count": session_over,
                "under_count": session_under
            })
    elif inventory_last_session and not inventory_last_session.is_active:
        inventory_status = "completed"
    
    inventory_data = {
        "status": inventory_status,
        "active_sessions": inventory_sessions_list,
        "last_session": {
            "id": inventory_last_session.id,
            "mode": inventory_last_session.mode.value,
            "started_at": inventory_last_session.started_at.isoformat(),
            "ended_at": inventory_last_session.ended_at.isoformat() if inventory_last_session.ended_at else None,
            "is_active": inventory_last_session.is_active
        } if inventory_last_session else None
    }
    
    return {
        "categories": overview,
        "inventory": inventory_data  # ⭐ NUEVA SECCIÓN
    }


@router.delete("/sessions/cleanup/dev")
async def cleanup_dev_sessions(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete all sessions that have no scan records (for development cleanup)
    """
    # Find sessions with no records
    empty_sessions = db.query(models.ScanSession).filter(
        models.ScanSession.user_id == current_user.id
    ).all()
    
    deleted_count = 0
    for session in empty_sessions:
        # Check if session has any records
        record_count = db.query(func.count(models.ScanRecord.id)).filter(
            models.ScanRecord.session_id == session.id
        ).scalar()
        
        if record_count == 0:
            db.delete(session)
            deleted_count += 1
    
    db.commit()
    
    return {
        "message": f"Deleted {deleted_count} empty sessions",
        "deleted_count": deleted_count
    }


@router.get("/sessions/{session_id}/inventory-summary")
def get_inventory_summary(
    session_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get inventory summary - groups scan records by article and sums quantities
    Optimized for INVENTORY mode (no BOM comparison)
    """
    session = db.query(models.ScanSession).filter(
        models.ScanSession.id == session_id,
        models.ScanSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Group by article and sum quantities
    grouped_records = db.query(
        models.ScanRecord.sap_article,
        models.ScanRecord.part_number,
        models.ScanRecord.description,
        models.ScanRecord.detected_category,  # ← AGREGAR
        func.sum(models.ScanRecord.quantity).label('total_quantity'),
        func.count(models.ScanRecord.id).label('scan_count'),
        func.min(models.ScanRecord.scanned_at).label('first_scan'),
        func.max(models.ScanRecord.scanned_at).label('last_scan')
    ).filter(
        models.ScanRecord.session_id == session_id
    ).group_by(
        models.ScanRecord.sap_article,
        models.ScanRecord.part_number,
        models.ScanRecord.description,
        models.ScanRecord.detected_category  # ← AGREGAR
    ).order_by(
        models.ScanRecord.sap_article
    ).all()

    items = []
    for record in grouped_records:
        items.append({
            "sap_article": record.sap_article,
            "part_number": record.part_number,
            "description": record.description,
            "detected_category": record.detected_category.value if record.detected_category else None,  # ← AGREGAR
            "total_quantity": float(record.total_quantity),
            "scan_count": record.scan_count,
            "first_scan": record.first_scan.isoformat(),
            "last_scan": record.last_scan.isoformat()
        })
    
    total_unique_items = len(items)
    total_scans = sum(item['scan_count'] for item in items)
    total_quantity = sum(item['total_quantity'] for item in items)
    
    return {
        "session": {
            "id": session.id,
            "mode": session.mode.value,
            "category": session.category.value if session.category else None,
            "started_at": session.started_at.isoformat(),
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "is_active": session.is_active
        },
        "summary": {
            "total_unique_items": total_unique_items,
            "total_scans": total_scans,
            "total_quantity": total_quantity
        },
        "items": items
    }

@router.get("/sessions/{session_id}/inventory-summary-by-category")
def get_inventory_summary_by_category(
    session_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get inventory summary grouped by detected category
    Shows breakdown: how many CCTV, CX, FIRE items in this session
    """
    session = db.query(models.ScanSession).filter(
        models.ScanSession.id == session_id,
        models.ScanSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Group by detected_category and article
    from sqlalchemy import case
    
    grouped_by_category = db.query(
        models.ScanRecord.detected_category,
        func.count(func.distinct(models.ScanRecord.sap_article)).label('unique_items'),
        func.sum(models.ScanRecord.quantity).label('total_quantity'),
        func.count(models.ScanRecord.id).label('scan_count')
    ).filter(
        models.ScanRecord.session_id == session_id
    ).group_by(
        models.ScanRecord.detected_category
    ).all()
    
    category_breakdown = []
    for cat, unique_items, total_qty, scan_count in grouped_by_category:
        # Get items for this category
        items = db.query(
            models.ScanRecord.sap_article,
            models.ScanRecord.part_number,
            models.ScanRecord.description,
            func.sum(models.ScanRecord.quantity).label('total_quantity'),
            func.count(models.ScanRecord.id).label('scan_count')
        ).filter(
            models.ScanRecord.session_id == session_id,
            models.ScanRecord.detected_category == cat
        ).group_by(
            models.ScanRecord.sap_article,
            models.ScanRecord.part_number,
            models.ScanRecord.description
        ).all()
        
        category_breakdown.append({
            "category": cat.value if cat else "UNKNOWN",
            "unique_items": unique_items,
            "total_quantity": float(total_qty or 0),
            "scan_count": scan_count,
            "items": [
                {
                    "sap_article": item.sap_article,
                    "part_number": item.part_number,
                    "description": item.description,
                    "detected_category": cat.value if cat else "UNKNOWN",  # ← AGREGAR (ya tenemos cat del loop)
                    "total_quantity": float(item.total_quantity),
                    "scan_count": item.scan_count
                }
                for item in items
            ]
        })
    
    return {
        "session": {
            "id": session.id,
            "mode": session.mode.value,
            "category": session.category.value if session.category else None,
            "started_at": session.started_at.isoformat(),
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "is_active": session.is_active
        },
        "category_breakdown": category_breakdown,
        "total_unique_items": sum(cb['unique_items'] for cb in category_breakdown),
        "total_quantity": sum(cb['total_quantity'] for cb in category_breakdown),
        "total_scans": sum(cb['scan_count'] for cb in category_breakdown)
    }

    # Al final de scan_router.py, después de la línea 918
@router.get("/last-update")
async def get_last_update(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get timestamp of last update to trigger frontend refresh"""
    # Get most recent scan record
    last_record = db.query(models.ScanRecord).join(
        models.ScanSession
    ).filter(
        models.ScanSession.user_id == current_user.id
    ).order_by(models.ScanRecord.scanned_at.desc()).first()
    
    # Get most recently updated session
    last_session = db.query(models.ScanSession).filter(
        models.ScanSession.user_id == current_user.id
    ).order_by(models.ScanSession.started_at.desc()).first()
    
    last_update = None
    if last_record:
        last_update = last_record.scanned_at
    if last_session and (not last_update or last_session.started_at > last_update):
        last_update = last_session.started_at
    
    return {
        "last_update": last_update.isoformat() if last_update else None,
        "timestamp": datetime.utcnow().isoformat()
    }