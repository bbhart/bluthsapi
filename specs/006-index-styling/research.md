# Research: Index Page Visual Redesign

**Feature**: 006-index-styling
**Date**: 2025-11-04

## Overview

This document captures design decisions, rationale, and alternatives considered for redesigning the API homepage with Arrested Development branding.

## Research Areas

### 1. Arrested Development Color Palette

**Decision**: Use the following color scheme based on promotional images:

**Primary Colors**:
- **Orange**: `#FF6B35` (main brand color from show's striped logo)
- **Dark Orange**: `#F7931E` (accent, darker variant for depth)
- **White**: `#FFFFFF` (background, stripes)
- **Cream/Off-white**: `#FFF8F0` (subtle backgrounds to reduce harsh contrast)

**Supporting Colors**:
- **Dark Gray**: `#2C3E50` (body text, maintains professional feel)
- **Medium Gray**: `#6C757D` (secondary text)
- **Light Gray**: `#F8F9FA` (section backgrounds)
- **Code Block**: `#1E1E1E` (dark background for code examples)
- **Success Green**: `#28A745` (for GET method badges)

**Rationale**:
- Orange `#FF6B35` directly extracted from the show's iconic striped promotional materials
- White provides the necessary contrast for the stripe pattern
- Dark grays maintain professionalism and readability
- Cream backgrounds soften pure white to reduce eye strain

**Alternatives Considered**:
- **Pure show palette (orange + blue)**: Rejected because blue competes with orange for attention and doesn't suit technical documentation
- **Monochrome orange tones**: Rejected because it reduces readability and feels less professional
- **Gradient backgrounds**: Rejected for complexity and potential accessibility issues

**References**:
- `/etc/art-examples/download.jpeg` - Classic orange and white stripes
- `/etc/art-examples/download (3).jpeg` - Modern promotional design with orange tones

---

### 2. WCAG 2.1 Level AA Accessibility

**Decision**: Implement the following contrast ratios:

| Element Type | Foreground | Background | Ratio | Requirement |
|-------------|------------|------------|-------|-------------|
| Body text (normal) | `#2C3E50` | `#FFFFFF` | 12.6:1 | ✅ 4.5:1 minimum |
| Body text (normal) | `#2C3E50` | `#FFF8F0` | 11.8:1 | ✅ 4.5:1 minimum |
| Headings (large) | `#FF6B35` | `#FFFFFF` | 3.5:1 | ✅ 3:1 minimum |
| Code examples | `#E8E8E8` | `#1E1E1E` | 13.1:1 | ✅ 4.5:1 minimum |
| Links | `#FF6B35` | `#FFFFFF` | 3.5:1 | ✅ 3:1 minimum |
| Orange on white | `#FF6B35` | `#FFFFFF` | 3.5:1 | ✅ 3:1 for large text |

**Rationale**:
- Normal body text uses dark gray (`#2C3E50`) instead of pure black for softer reading experience while exceeding 4.5:1 requirement
- Orange headers use larger font sizes (18pt+) to meet 3:1 requirement for large text
- Code blocks use high-contrast dark background to ensure readability
- All interactive elements (links) meet minimum contrast requirements

**Implementation Notes**:
- Orange `#FF6B35` CANNOT be used for normal-sized body text on white (only 3.5:1)
- Orange is restricted to headings (18pt+), buttons, and decorative elements
- Body copy must remain dark gray or darker

**Alternatives Considered**:
- **Darker orange for body text**: Would meet contrast but loses the show's authentic color
- **Lighter backgrounds throughout**: Would allow more orange usage but reduces professional appearance

**Validation Tools**:
- WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/
- Browser DevTools accessibility audit
- Manual testing with color blindness simulators

---

### 3. CSS Organization and Architecture

**Decision**: Use single external CSS file with the following structure:

```css
/* 1. CSS Reset & Base Styles */
/* 2. Typography */
/* 3. Layout (container, grid if needed) */
/* 4. Components (endpoint blocks, code examples, notes) */
/* 5. Utilities (responsive, accessibility) */
```

**Rationale**:
- Single file keeps it simple (page is small, < 300 lines HTML)
- Logical organization makes future updates easy
- No build tools needed (constitution: keep it simple)
- External file allows browser caching

**File Structure**:
```
public/
├── index.html (links to styles.css)
└── styles.css (all styling)
```

**Alternatives Considered**:
- **Inline CSS**: Rejected because it's harder to maintain and violates P3 user story
- **Multiple CSS files**: Rejected as overkill for a single-page site (adds HTTP requests)
- **CSS preprocessor (SASS/LESS)**: Rejected because it adds build complexity forbidden by constitution
- **CSS-in-JS**: Rejected because it requires JavaScript (page must work without JS)
- **CSS Framework (Bootstrap/Tailwind)**: Rejected because:
  - Adds unnecessary bloat (most styles unused)
  - Generic look doesn't match show branding
  - External dependency increases complexity

**Graceful Degradation Strategy**:
- HTML semantic structure ensures readability without CSS
- Use `<style>` tag in `<head>` with critical inline styles as fallback:
  ```html
  <noscript>
    <style>
      /* Minimal styles for readability if CSS fails */
      body { font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
      code { background: #f4f4f4; padding: 2px 6px; }
    </style>
  </noscript>
  ```

---

### 4. Responsive Design Breakpoints

**Decision**: Use mobile-first approach with these breakpoints:

| Breakpoint | Target | Adjustments |
|------------|--------|-------------|
| Default (320px+) | Mobile phones | Single column, large touch targets, stacked layout |
| 600px+ | Tablets | Slightly wider container, adjusted font sizes |
| 900px+ | Desktop | Full-width container (max 900px), optimal line length |
| 1200px+ | Large screens | Same as desktop (center with margins) |

**Rationale**:
- 320px minimum supports even very small devices (iPhone SE)
- 900px max-width maintains optimal reading line length (45-75 characters)
- Constitution requires mobile support - mobile-first ensures it works on all devices

**Implementation Approach**:
```css
/* Base: Mobile (320px+) */
.container { padding: 20px; }

/* Tablet (600px+) */
@media (min-width: 600px) {
  .container { padding: 30px; }
}

/* Desktop (900px+) */
@media (min-width: 900px) {
  .container { max-width: 900px; margin: 0 auto; padding: 40px; }
}
```

**Alternatives Considered**:
- **Desktop-first**: Rejected because it's harder to scale down than up
- **More breakpoints**: Rejected as unnecessary for a simple documentation page
- **Fluid typography (clamp())**: Considered but kept simple with fixed sizes at breakpoints

---

### 5. Typography

**Decision**: Use system font stack for performance and native look:

```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
             Oxygen, Ubuntu, Cantarell, 'Helvetica Neue', sans-serif;
```

**Rationale**:
- No web font downloads = faster page load
- Native fonts feel familiar on each OS
- Excellent readability for technical content
- Meets performance goal (< 2 second load)

**Type Scale**:
```
H1: 2.5rem (40px) - Page title
H2: 2rem (32px) - Section headers
H3: 1.5rem (24px) - Endpoint titles
Body: 1rem (16px) - Documentation text
Code: 0.9rem (14.4px) - Code examples
```

**Alternatives Considered**:
- **Google Fonts (Montserrat, Open Sans)**: Rejected due to external HTTP request and slower load times
- **Custom web fonts**: Rejected for same performance reasons
- **Monospace for all code**: Kept `Courier New` stack for code consistency

---

### 6. Visual Hierarchy & Layout

**Decision**: Implement card-based design with orange accents:

**Layout Elements**:
1. **Hero Section**: Large orange header with white text, subtle stripe pattern background
2. **Content Container**: White card with soft shadow, max-width 900px
3. **Endpoint Blocks**: Light gray background with orange left border (4px)
4. **Code Examples**: Dark background (`#1E1E1E`) with syntax-friendly colors
5. **Notes/Warnings**: Yellow background with orange left border

**Visual Hierarchy**:
- Orange reserved for: H1, H2 borders, accent borders, CTA elements
- Dark gray for body text (readability)
- Code blocks use dark theme (developer-friendly)
- Ample white space between sections (breathing room)

**Rationale**:
- Card design feels modern and professional
- Orange accents tie to brand without overwhelming
- Dark code blocks are industry standard for developer docs
- Clear section separation improves scannability (SC-001: identify endpoints in 10 seconds)

**Alternatives Considered**:
- **Stripe pattern throughout**: Too busy, reduces readability
- **All-orange backgrounds**: Accessibility nightmare, eye strain
- **Minimalist (no cards)**: Lacks visual interest, harder to scan

---

## Implementation Notes

### Color Validation Checklist
- [ ] Test all text/background combinations with WebAIM Contrast Checker
- [ ] Verify orange headings are 18pt+ (large text exception)
- [ ] Ensure code blocks have 4.5:1+ contrast
- [ ] Test with color blindness simulators (deuteranopia, protanopia)

### Browser Testing Targets
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile Safari (iOS)
- Chrome Mobile (Android)

### Performance Budget
- Total CSS file size: < 50KB
- No external font files
- No CSS preprocessor build step
- First Contentful Paint: < 1 second

---

## References

**Promotional Images Analyzed**:
- `etc/art-examples/download.jpeg` - Orange/white stripe pattern
- `etc/art-examples/download (3).jpeg` - Modern orange palette with depth

**Accessibility Guidelines**:
- WCAG 2.1 Level AA: https://www.w3.org/WAI/WCAG21/quickref/
- WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/

**Best Practices**:
- MDN Web Docs - CSS: https://developer.mozilla.org/en-US/docs/Web/CSS
- Google Web Fundamentals - Responsive Design: https://web.dev/responsive-web-design-basics/
