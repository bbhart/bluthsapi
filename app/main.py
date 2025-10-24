"""FastAPI application for Arrested Development Quotes API."""

import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.models import Quote, QuoteResponse, ErrorResponse
from app.services import (
    load_quotes,
    get_random_quote,
    filter_by_speaker,
    filter_meme_quotes,
    build_quote_response,
    build_error_response,
)
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global quotes storage
quotes_db: list[Quote] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load quotes on startup."""
    global quotes_db
    try:
        quotes_db = load_quotes()
        logger.info(f"Loaded {len(quotes_db)} quotes from quotes.json")
    except Exception as e:
        logger.error(f"Failed to load quotes: {e}")
        raise
    yield


# Create FastAPI app
app = FastAPI(
    title="Arrested Development Quotes API",
    description="A read-only REST API serving memorable quotes from the TV show Arrested Development",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "quotes_loaded": len(quotes_db)
    }


@app.get(
    "/api/quotes/random",
    response_model=QuoteResponse,
    responses={
        200: {"description": "Successfully retrieved random quote"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["Quotes"]
)
async def random_quote(response: Response):
    """Get a random quote from all available quotes."""
    logger.info("Random quote requested")

    # Add cache control headers
    response.headers["Cache-Control"] = "public, max-age=3600"

    if not quotes_db:
        logger.error("No quotes available in database")
        raise HTTPException(
            status_code=500,
            detail="Failed to load quotes data"
        )

    quote = get_random_quote(quotes_db)
    if not quote:
        logger.error("Failed to select random quote")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve quote"
        )

    return build_quote_response(quote, settings.s3_base_url)


@app.get(
    "/api/quotes/meme",
    response_model=QuoteResponse,
    responses={
        200: {"description": "Successfully retrieved meme quote"},
        404: {"model": ErrorResponse, "description": "No meme quotes available"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["Quotes"]
)
async def meme_quote(response: Response):
    """Get a random quote that has an associated image."""
    logger.info("Meme quote requested")

    # Add cache control headers
    response.headers["Cache-Control"] = "public, max-age=3600"

    if not quotes_db:
        logger.error("No quotes available in database")
        raise HTTPException(
            status_code=500,
            detail="Failed to load quotes data"
        )

    meme_quotes = filter_meme_quotes(quotes_db)

    if not meme_quotes:
        logger.warning("No meme quotes available")
        raise HTTPException(
            status_code=404,
            detail="No meme quotes available"
        )

    quote = get_random_quote(meme_quotes)
    if not quote:
        logger.error("Failed to select meme quote")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve quote"
        )

    return build_quote_response(quote, settings.s3_base_url)


@app.get(
    "/api/quotes/{speaker}",
    response_model=QuoteResponse,
    responses={
        200: {"description": "Successfully retrieved quote for speaker"},
        404: {"model": ErrorResponse, "description": "No quotes found for speaker"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["Quotes"]
)
async def quote_by_speaker(speaker: str, response: Response):
    """Get a random quote filtered by speaker (case-insensitive)."""
    logger.info(f"Quote requested for speaker: {speaker}")

    # Add cache control headers
    response.headers["Cache-Control"] = "public, max-age=3600"

    if not quotes_db:
        logger.error("No quotes available in database")
        raise HTTPException(
            status_code=500,
            detail="Failed to load quotes data"
        )

    filtered_quotes = filter_by_speaker(quotes_db, speaker)

    if not filtered_quotes:
        logger.warning(f"No quotes found for speaker: {speaker}")
        raise HTTPException(
            status_code=404,
            detail=f"No quotes found for character: {speaker}"
        )

    quote = get_random_quote(filtered_quotes)
    if not quote:
        logger.error(f"Failed to select quote for speaker: {speaker}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve quote"
        )

    return build_quote_response(quote, settings.s3_base_url)


# Mount static files (serve index.html at root)
public_dir = Path(__file__).parent.parent / "public"
if public_dir.exists():
    app.mount("/", StaticFiles(directory=str(public_dir), html=True), name="static")
    logger.info(f"Mounted static files from {public_dir}")
