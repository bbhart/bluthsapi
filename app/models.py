"""Pydantic models for Arrested Development Quotes API."""

from typing import Optional
from pydantic import BaseModel, Field


class Quote(BaseModel):
    """Quote entity as stored in quotes.json."""

    id: str = Field(..., description="Unique identifier for the quote")
    quote: str = Field(..., max_length=1000, description="The actual quote text")
    speakers: str = Field(
        "",
        description=(
            "Characters speaking in the quote, comma-separated in order of "
            "appearance (e.g. 'Lucille,Michael'). Empty when unknown. Names "
            "must match app/data/list-of-characters.txt."
        ),
    )
    context: Optional[str] = Field(None, description="Episode reference or situational context")
    imageUrl: Optional[str] = Field(None, description="Relative path to image (S3 key)")


class QuoteResponse(BaseModel):
    """Success response wrapping a quote."""

    data: Quote


class ErrorResponse(BaseModel):
    """Error response structure.

    The field is `detail` because that is what FastAPI's HTTPException emits.
    This model exists only to document that shape in the OpenAPI spec; nothing
    constructs it. Renaming the field would silently break every client that
    reads the published spec.
    """

    detail: str = Field(..., description="Human-readable error message")
