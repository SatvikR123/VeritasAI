from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl

class ArticleSource(BaseModel):
    id: Optional[str] = Field(None, description="Unique identifier of the source if available (e.g. from NewsAPI)")
    name: str = Field(..., description="Name of the news source or publisher")
    domain: Optional[str] = Field(None, description="Domain name of the source (e.g. cnn.com)")
    url: Optional[HttpUrl] = Field(None, description="Base URL of the source website")

class Article(BaseModel):
    id: Optional[str] = Field(None, description="Unique identifier of the article (UUID or hash of URL)")
    title: str = Field(..., description="Title of the article")
    author: Optional[str] = Field(None, description="Author(s) of the article")
    source: ArticleSource = Field(..., description="The publishing source of the article")
    published_at: Optional[datetime] = Field(None, description="Publication timestamp of the article")
    url: HttpUrl = Field(..., description="Direct URL to the article")
    content: str = Field(..., description="Full text content of the article")
    description: Optional[str] = Field(None, description="Brief description or snippet of the article")
    url_to_image: Optional[HttpUrl] = Field(None, description="URL of the main image of the article")
    language: str = Field("en", description="Language code of the article")

class ArticleCluster(BaseModel):
    cluster_id: str = Field(..., description="Unique identifier for the cluster (e.g., UUID or hash)")
    topic: str = Field(..., description="Main topic or headline summarizing the cluster")
    summary: Optional[str] = Field(None, description="Preliminary summary of the cluster")
    articles: List[Article] = Field(default_factory=list, description="List of articles belonging to this cluster")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of when the cluster was created")
