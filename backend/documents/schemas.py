"""Pydantic v2 schemas for documents."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    """A document record as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    chunk_count: int
    created_at: datetime


class UploadResponse(BaseModel):
    """Result of a successful upload."""

    message: str
    document: DocumentResponse
