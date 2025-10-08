from fastapi import APIRouter, Depends, HTTPException, status
from google.cloud import firestore
from typing import List, Optional
from ..firestore_client import get_db
from .. import schemas, auth
from ..firestore_models import FirestoreArticle
from ..models import CategoryEnum

router = APIRouter(prefix="/articles", tags=["Articles"])


@router.post("/", response_model=schemas.Article, status_code=status.HTTP_201_CREATED)
async def create_article(
    article: schemas.ArticleCreate,
    db: firestore.Client = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Create a new article"""
    # Check if article already exists with same sap_article and category
    existing = db.collection('articles')\
        .where('sap_article', '==', article.sap_article)\
        .where('category', '==', article.category.value)\
        .limit(1).stream()
    
    if list(existing):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Article {article.sap_article} already exists in category {article.category}"
        )
    
    article_dict = FirestoreArticle.to_dict(
        sap_article=article.sap_article,
        part_number=article.part_number,
        description=article.description,
        category=article.category
    )
    
    _, doc_ref = db.collection('articles').add(article_dict)
    article_dict['id'] = doc_ref.id
    
    return FirestoreArticle.to_schema(article_dict)


@router.get("/", response_model=List[schemas.Article])
async def get_articles(
    category: Optional[CategoryEnum] = None,
    db: firestore.Client = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Get all articles, optionally filtered by category"""
    collection_ref = db.collection('articles')
    
    if category:
        docs = collection_ref.where('category', '==', category.value).stream()
    else:
        docs = collection_ref.stream()
    
    articles = []
    for doc in docs:
        article_data = doc.to_dict()
        article_data['id'] = doc.id
        articles.append(FirestoreArticle.to_schema(article_data))
    
    return articles


@router.get("/{article_id}", response_model=schemas.Article)
async def get_article(
    article_id: str,
    db: firestore.Client = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Get article by ID"""
    doc = db.collection('articles').document(article_id).get()
    
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    
    article_data = doc.to_dict()
    article_data['id'] = doc.id
    return FirestoreArticle.to_schema(article_data)


@router.put("/{article_id}", response_model=schemas.Article)
async def update_article(
    article_id: str,
    article_update: schemas.ArticleCreate,
    db: firestore.Client = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Update an article"""
    doc_ref = db.collection('articles').document(article_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    
    from datetime import datetime
    update_data = {
        'sap_article': article_update.sap_article,
        'part_number': article_update.part_number,
        'description': article_update.description,
        'category': article_update.category.value,
        'updated_at': datetime.utcnow()
    }
    
    doc_ref.update(update_data)
    
    updated_doc = doc_ref.get()
    article_data = updated_doc.to_dict()
    article_data['id'] = updated_doc.id
    
    return FirestoreArticle.to_schema(article_data)


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    article_id: str,
    db: firestore.Client = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Delete an article"""
    doc_ref = db.collection('articles').document(article_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    
    doc_ref.delete()
    return None
