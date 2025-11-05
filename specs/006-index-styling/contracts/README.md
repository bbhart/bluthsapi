# Contracts: Index Page Visual Redesign

**Feature**: 006-index-styling
**Date**: 2025-11-04

## Overview

This feature involves only visual (HTML/CSS) changes. No API contracts are added or modified.

## Static File Contracts

While there are no API contracts, the static files must adhere to the following contracts:

### HTML Contract (`public/index.html`)

**Purpose**: API documentation homepage

**Requirements**:
1. **Valid HTML5**: Must pass W3C HTML validator
2. **Semantic structure**: Proper use of heading hierarchy (H1 → H2 → H3)
3. **Accessibility**:
   - All images must have alt text
   - Proper ARIA labels where needed
   - Keyboard navigation support
4. **Content preservation**: Must include all existing API documentation
   - Endpoint descriptions
   - Code examples
   - Error handling documentation
5. **Link to external CSS**: `<link rel="stylesheet" href="styles.css">`
6. **Graceful degradation**: Readable without CSS via semantic HTML

**Structure**:
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Arrested Development Quotes API</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <!-- Content sections -->
</body>
</html>
```

---

### CSS Contract (`public/styles.css`)

**Purpose**: Visual styling for API documentation

**Requirements**:
1. **Valid CSS3**: Must pass W3C CSS validator
2. **Accessibility**:
   - All text/background combinations meet WCAG 2.1 Level AA contrast ratios
   - Normal text: minimum 4.5:1
   - Large text (18pt+): minimum 3:1
3. **Responsive design**:
   - Mobile-first approach
   - Works on screens 320px - 2560px wide
   - Breakpoints at 600px, 900px, 1200px
4. **Performance**:
   - Total file size < 50KB
   - No external dependencies (fonts, images)
5. **Browser compatibility**:
   - Modern browsers (Chrome, Firefox, Safari, Edge - last 2 versions)
   - No vendor prefixes for ancient browsers
6. **Organization**:
   ```css
   /* 1. CSS Reset & Base */
   /* 2. Typography */
   /* 3. Layout */
   /* 4. Components */
   /* 5. Responsive */
   ```

**Color Palette Contract**:
```css
:root {
  /* Primary brand colors */
  --color-orange: #FF6B35;
  --color-dark-orange: #F7931E;
  --color-white: #FFFFFF;
  --color-cream: #FFF8F0;

  /* Text colors */
  --color-text-dark: #2C3E50;
  --color-text-medium: #6C757D;
  --color-text-light: #F8F9FA;

  /* Functional colors */
  --color-code-bg: #1E1E1E;
  --color-success: #28A745;
}
```

---

## Validation Contract

Before deployment, the following validations must pass:

### HTML Validation
```bash
# Validate HTML5 structure
python3 -c "from html.parser import HTMLParser; HTMLParser().feed(open('public/index.html').read())"
```

### CSS Validation
```bash
# Validate CSS syntax (basic check)
python3 -c "import re; assert len(open('public/styles.css').read()) < 50000, 'CSS exceeds 50KB'"
```

### Accessibility Validation
- Manual contrast ratio checks using WebAIM Contrast Checker
- Test with browser DevTools accessibility audit
- Verify keyboard navigation works

### Visual Validation
- Load `http://localhost:8000/` and verify all sections render correctly
- Test on multiple screen sizes (mobile, tablet, desktop)
- Test on multiple browsers (Chrome, Firefox, Safari, Edge)

---

## API Contract (Unchanged)

The existing API contracts remain unchanged:

**Endpoints** (no modifications):
- `GET /api/quotes/random`
- `GET /api/quotes/{character}`
- `GET /api/quotes/meme`

**Response Format** (no modifications):
```json
{
  "data": {
    "id": "quote-001",
    "quote": "There are dozens of us!",
    "primarySpeaker": "Tobias"
  }
}
```

**Static File Serving** (no modifications):
- FastAPI `StaticFiles` middleware serves `public/` directory at root `/`
- `index.html` accessible at `http://localhost:8000/` or `https://api.lucille2.com/`

---

**Summary**: No API contract changes. Static file contracts define structure, accessibility, and performance requirements for HTML/CSS files.
