# Quickstart: Pretty Quote Display Page

**Feature**: 008-prettyquote-page
**Date**: 2025-12-03

## What You're Building

A single HTML page (`prettyquote.html`) that:
1. Fetches a random Arrested Development quote from the API
2. Displays only the quote text (no metadata)
3. Shows the quote large and centered (~50% viewport height)
4. Provides a Copy button to copy the quote to clipboard
5. Shows "Copied!" feedback when copy succeeds

## Prerequisites

- The existing API must be running (local dev or production)
- Modern browser with Clipboard API support

## File to Create

```
public/prettyquote.html
```

## Implementation Outline

### HTML Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quote</title>
    <style>
        /* Inline CSS for self-contained file */
    </style>
</head>
<body>
    <main class="quote-container">
        <p id="quote" class="quote-text">Loading...</p>
    </main>
    <button id="copy-btn" class="copy-button">Copy</button>
    <script>
        /* Inline JavaScript */
    </script>
</body>
</html>
```

### Key CSS Requirements

1. **Full viewport layout**: `min-height: 100vh`, flexbox centering
2. **Quote sizing**: `font-size: clamp(1.5rem, 5vw, 4rem)`, `max-height: 50vh`
3. **Copy button**: `position: fixed`, `bottom: 20px`, centered horizontally
4. **Touch-friendly**: Minimum 48px button height, adequate padding

### Key JavaScript Requirements

1. **On page load**: Fetch `/api/quotes/random`, extract `data.quote`
2. **Display quote**: Set `#quote` text content
3. **Copy button click**: Use `navigator.clipboard.writeText()`
4. **Feedback**: Change button text to "Copied!" for 1.5 seconds
5. **Error handling**: Display friendly message if API fails

## Testing Checklist

- [ ] Quote loads on page open
- [ ] Quote is centered horizontally and vertically
- [ ] Quote consumes ~50% of viewport on mobile
- [ ] Copy button visible at bottom of screen
- [ ] Copy button copies text to clipboard
- [ ] Button shows "Copied!" feedback
- [ ] Refresh loads a new quote
- [ ] Error message shows if API unavailable
- [ ] Page works on iOS Safari
- [ ] Page works on Android Chrome

## What NOT to Do

- Do not link to this page from index.html
- Do not add this page to any navigation
- Do not mention this page in documentation
- Do not display quote metadata (speaker, ID, context)
