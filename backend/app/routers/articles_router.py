from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, auth
from ..database import get_db
from ..excel_handler import parse_articles_excel

router = APIRouter(prefix="/articles", tags=["articles"])


@router.post("/upload", response_model=schemas.UploadResponse)
async def upload_articles(
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Upload article database from Excel file"""
    if not file.filename.endswith(('.xlsx', '.xls', '.xlsm')):
            raise HTTPException(status_code=400, detail="File must be an Excel file (.xlsx or .xls)")
    
    try:
        content = await file.read()
        articles_data = parse_articles_excel(content)
        
        # Delete existing articles and commit
        deleted_count = db.query(models.Article).delete()
        db.commit()
        print(f"Deleted {deleted_count} existing articles")
        
        # Check for duplicates in uploaded file (same SAP + same Category)
        article_keys = [(a['sap_article'], a['category']) for a in articles_data]
        if len(article_keys) != len(set(article_keys)):
            duplicates = [x for x in article_keys if article_keys.count(x) > 1]
            raise ValueError(f"Excel file contains duplicate (SAP Article + Category) combinations: {list(set(duplicates))}")
        
        # Insert new articles
        created_articles = []
        for article_data in articles_data:
            db_article = models.Article(**article_data)
            db.add(db_article)
            created_articles.append(article_data)
        
        db.commit()
        print(f"Successfully inserted {len(created_articles)} articles")
        
        return schemas.UploadResponse(
            message=f"Successfully uploaded {len(created_articles)} articles",
            count=len(created_articles),
            items=created_articles[:10]  # Return first 10 as preview
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.get("/", response_model=List[schemas.Article])
def get_articles(
    skip: int = 0,
    limit: int = 100,
    category: str = None,
    search: str = None,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get all articles with optional filtering"""
    query = db.query(models.Article)
    
    if category:
        query = query.filter(models.Article.category == category)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (models.Article.sap_article.ilike(search_pattern)) |
            (models.Article.part_number.ilike(search_pattern)) |
            (models.Article.description.ilike(search_pattern))
        )
    
    return query.offset(skip).limit(limit).all()


@router.get("/{sap_article}", response_model=schemas.Article)
def get_article(
    sap_article: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get article by SAP article number"""
    article = db.query(models.Article).filter(
        models.Article.sap_article == sap_article
    ).first()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return article


@router.get("/stats/count")
def get_article_stats(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get article statistics"""
    total = db.query(models.Article).count()
    by_category = {}
    
    for category in models.CategoryEnum:
        count = db.query(models.Article).filter(
            models.Article.category == category
        ).count()
        by_category[category.value] = count
    
    return {
        "total": total,
        "by_category": by_category
    }


@router.delete("/clear")
def clear_all_articles(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete all articles from database"""
    deleted_count = db.query(models.Article).delete()
    db.commit()
    
    return {
        "message": f"Successfully deleted {deleted_count} articles",
        "deleted_count": deleted_count
    }
