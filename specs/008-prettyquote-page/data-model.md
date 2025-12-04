# Data Model: Pretty Quote Display Page

**Feature**: 008-prettyquote-page
**Date**: 2025-12-03

## Overview

This feature consumes an existing API endpoint and does not introduce new data entities. The page is a read-only consumer of the existing quote data structure.

## Consumed Data Structure

### API Response (from `/api/quotes/random`)

```json
{
  "data": {
    "id": "string",
    "quote": "string",
    "primarySpeaker": "string (optional)",
    "speakers": ["string"] (optional),
    "context": "string (optional)",
    "imageUrl": "string (optional)"
  }
}
```

### Data Used by This Feature

| Field | Used | Purpose |
|-------|------|---------|
| `data.quote` | Yes | Displayed as the main content |
| `data.id` | No | Not displayed per spec |
| `data.primarySpeaker` | No | Not displayed per spec |
| `data.speakers` | No | Not displayed per spec |
| `data.context` | No | Not displayed per spec |
| `data.imageUrl` | No | Not displayed per spec |

## Client-Side State

The page maintains minimal transient state:

| State | Type | Purpose |
|-------|------|---------|
| `currentQuote` | string | The quote text currently displayed |
| `isLoading` | boolean | Loading state during API fetch |
| `hasError` | boolean | Error state if API fails |
| `isCopied` | boolean | Temporary state for copy feedback |

## No New Entities

This feature:
- Does not create new database entities
- Does not modify existing entities
- Does not require new API endpoints
- Does not persist any data

## Contracts

No new API contracts required. This feature uses the existing `/api/quotes/random` endpoint documented in the main API specification.
