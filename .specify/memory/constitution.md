# Bluths API Constitution

## Core Principles

### I. Read-Only Access
All endpoints must be GET requests only. No POST, PUT, PATCH, or DELETE operations. API serves data retrieval exclusively.

### II. Public Access
No authentication required. All quote data is publicly accessible without API keys or tokens.

### III. RESTful Design
Resource-based URLs following REST conventions. Proper HTTP status codes. Consistent JSON response structure.

### IV. Quote Data Structure
Every quote includes: quote text. Optional fields: primary speaker, one or more speakers, context, image url.

### V. Simple Error Handling
Use standard HTTP status codes: 200 (success), 404 (not found), 500 (server error). Return descriptive error messages in JSON format.

## API Standards

Do not allow for fetching of all quotes. There should be only one quote per request.

### Required Endpoints
- GET /quotes/random - Get random quote
- GET /quotes/<primary speaker> - Get random quote filtered by the primary speaker
- GET /quotes/meme - Get random quote where there's an image url 

### Response Format
Success: `{ "data": { ... } }` with status 200
Error: `{ "error": "message" }` with appropriate status code

## Documentation

Basic README with endpoint list and example responses required.

## Governance

This constitution defines minimal viable quote API. 
All endpoints must remain read-only and publicly accessible.
Serving costs should be minimized. This is not expected to be a high use API.

**Version**: 1.0.0 | **Ratified**: 2025-10-24 | **Last Amended**: 2025-10-24
