"""Pydantic models for Arrested Development Quotes API."""

from typing import Optional
from pydantic import BaseModel, Field


class Quote(BaseModel):
    """Quote entity as stored in quotes.json."""

    id: str = Field(..., description="Unique identifier for the quote")
    quote: str = Field(..., max_length=1000, description="The actual quote text")
    primarySpeaker: Optional[str] = Field(None, description="Main character delivering the quote")
    speakers: Optional[list[str]] = Field(None, description="All characters involved in the quote")
    context: Optional[str] = Field(None, description="Episode reference or situational context")
    imageUrl: Optional[str] = Field(None, description="Relative path to image (S3 key)")


class QuoteResponse(BaseModel):
    """Success response wrapping a quote."""

    data: Quote


class ErrorResponse(BaseModel):
    """Error response structure."""

    error: str = Field(..., description="Human-readable error message")
