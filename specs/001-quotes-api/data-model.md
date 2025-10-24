# Data Model: Arrested Development Quotes API

**Feature**: 001-quotes-api
**Date**: 2025-10-24
**Purpose**: Define structure for quotes.json and runtime entities

## Overview

This API uses a static JSON file (`quotes.json`) as its data source. The file contains an array of Quote objects that are loaded into memory and filtered/selected at runtime.

---

## Entity: Quote

Represents a single memorable line from Arrested Development.

### Fields

| Field | Type | Required | Description | Validation Rules |
|-------|------|----------|-------------|------------------|
| `id` | string | Yes | Unique identifier for the quote | Non-empty string, unique within dataset |
| `quote` | string | Yes | The actual quote text | Non-empty string, max 1000 characters |
| `primarySpeaker` | string | No | Main character delivering the quote | If present: non-empty string |
| `speakers` | array[string] | No | All characters involved in the quote | If present: array of non-empty strings |
| `context` | string | No | Episode reference or situational context | If present: non-empty string |
| `imageUrl` | string | No | Relative path to image (S3 key) | If present: valid path string (no protocol/domain) |

### Example Quote Objects

```json
{
  "id": "quote-001",
  "quote": "I've made a huge mistake.",
  "primarySpeaker": "Gob",
  "speakers": ["Gob"],
  "context": "Season 1, Episode 1 - Pilot"
}
```

```json
{
  "id": "quote-042",
  "quote": "There's always money in the banana stand.",
  "primarySpeaker": "George Sr.",
  "speakers": ["George Sr.", "Michael"],
  "context": "Season 1, Episode 2 - Top Banana",
  "imageUrl": "banana-stand.jpg"
}
```

```json
{
  "id": "quote-099",
  "quote": "I blue myself.",
  "primarySpeaker": "Tobias",
  "imageUrl": "tobias-blue.jpg"
}
```

### Validation Rules

- **id**: Must be unique across all quotes. Recommended format: `quote-XXX` where XXX is zero-padded number
- **quote**: Required. Cannot be empty. Reasonable max length 1000 chars (very long quotes)
- **primarySpeaker**: Optional. Used for `/api/quotes/:speaker` filtering. Case-insensitive matching required (FR-016)
- **speakers**: Optional. Array for quotes with multiple characters involved
- **context**: Optional. Helps users understand when/where quote was said
- **imageUrl**: Optional. Relative path only (no `https://`). Will be prefixed with S3_BASE_URL at runtime

---

## Data File Structure

### File: `app/data/quotes.json`

**Initial Placeholder** (created with this feature):
```json
{
  "quotes": [
    {
      "id": "quote-001",
      "quote": "There are dozens of us! DOZENS!!!",
      "primarySpeaker": "Tobias"
    }
  ]
}
```

**Example with Full Dataset** (to be populated in future feature):
```json
{
  "quotes": [
    {
      "id": "quote-001",
      "quote": "There are dozens of us! DOZENS!!!",
      "primarySpeaker": "Tobias"
    },
    {
      "id": "quote-002",
      "quote": "I've made a huge mistake.",
      "primarySpeaker": "Gob",
      "speakers": ["Gob"],
      "context": "Season 1, Episode 1 - Pilot"
    },
    {
      "id": "quote-003",
      "quote": "There's always money in the banana stand.",
      "primarySpeaker": "George Sr.",
      "speakers": ["George Sr.", "Michael"],
      "context": "Season 1, Episode 2 - Top Banana",
      "imageUrl": "banana-stand.jpg"
    }
  ]
}
```

**Structure Notes**:
- Root object has single `quotes` array
- Array contains Quote objects
- Placeholder file with single Tobias quote will be created as part of this feature
- Full quotes dataset will be added in a future feature

---

## Runtime Behavior

### Loading Quotes

```javascript
// In Cloudflare Function
import quotesData from '../data/quotes.json';
const quotes = quotesData.quotes;
```

### Random Selection

```javascript
function getRandomQuote(quotesArray) {
  const randomIndex = Math.floor(Math.random() * quotesArray.length);
  return quotesArray[randomIndex];
}
```

### Character Filtering (Case-Insensitive)

```javascript
function filterBySpeaker(quotesArray, speaker) {
  const speakerLower = speaker.toLowerCase();
  return quotesArray.filter(q =>
    q.primarySpeaker?.toLowerCase() === speakerLower
  );
}
```

### Meme Filtering

```javascript
function filterMemeQuotes(quotesArray) {
  return quotesArray.filter(q => q.imageUrl !== undefined && q.imageUrl !== null);
}
```

### Image URL Construction

```javascript
function buildImageUrl(imageUrl, s3BaseUrl) {
  if (!imageUrl) return null;
  return `${s3BaseUrl.replace(/\/$/, '')}/${imageUrl}`;
}
```

---

## Response Entity: QuoteResponse

The Quote entity is transformed into a response format before being returned to API consumers.

### Success Response Structure

```json
{
  "data": {
    "id": "quote-001",
    "quote": "I've made a huge mistake.",
    "primarySpeaker": "Gob",
    "speakers": ["Gob"],
    "context": "Season 1, Episode 1 - Pilot",
    "imageUrl": "https://bucket.s3.amazonaws.com/banana-stand.jpg"
  }
}
```

### Response Transformation Rules

1. Wrap quote object in `{ "data": { ... } }` envelope (per constitution)
2. If `imageUrl` is present in Quote, prefix with S3_BASE_URL environment variable
3. If `imageUrl` is null/undefined, omit field from response (don't send `null`)
4. Include only populated fields (omit `null` or `undefined` fields)

### Error Response Structure

```json
{
  "error": "No quotes found for character: Hermano"
}
```

**Error Response Rules**:
- Use `{ "error": "message" }` format (per constitution)
- Include descriptive, user-friendly message (FR-011)
- HTTP status code in response header (404, 500)

---

## Data Constraints

### Volume
- **Estimated size**: 50-200 quotes initially (can grow over time)
- **File size**: ~50KB for 200 quotes (well within serverless limits)
- **Memory**: Entire dataset loaded into memory (<1MB), acceptable for serverless

### Performance
- **Load time**: JSON parsed once per cold start, cached in memory
- **Filter time**: O(n) linear scan acceptable for <1000 quotes
- **Random selection**: O(1) constant time

### Growth Considerations
- If dataset grows beyond 1000 quotes, consider indexing by primarySpeaker
- File remains manageable up to ~5000 quotes (~250KB)
- No database needed for this scale

---

## State Management

### Stateless Operation
- No quote state changes (read-only API per constitution)
- No user state (no authentication per constitution)
- No session management required
- Each request is independent

### Caching
- Cloudflare CDN caches GET responses by default
- Consider `Cache-Control: public, max-age=3600` header for quote responses
- Cache invalidation happens on new deployment (quotes.json update)

---

## Future Considerations

### Out of Scope (Current Feature)
- Quote creation/editing interface (read-only API)
- Database migration (static file sufficient)
- User-submitted quotes (no authentication)
- Quote ratings/favorites (stateless API)

### Potential Future Enhancements
- Additional filtering fields (season, episode number)
- Full-text search in quote text
- Multiple image URLs per quote
- Character metadata (actor name, bio)

---

## Alignment with Spec

This data model satisfies:
- **FR-002**: Load data from static JSON file
- **FR-016**: Case-insensitive character matching
- **Constitution Principle IV**: Quote includes text (required), speaker/context/imageUrl (optional)
- **Key Entities**: Quote and Character/Speaker entities defined in spec
