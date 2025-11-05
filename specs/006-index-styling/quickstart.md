# Quickstart: Index Page Visual Redesign

**Feature**: 006-index-styling
**Branch**: `006-index-styling`
**Date**: 2025-11-04

## Overview

This guide walks you through implementing the visual redesign of the API homepage with Arrested Development's orange branding.

## Prerequisites

- Git repository cloned locally
- Text editor or IDE
- Web browser for testing
- Python 3.11+ (for running local server)

## Implementation Steps

### Step 1: Extract CSS from HTML

**Goal**: Separate existing inline styles into external CSS file

1. Open `public/index.html`
2. Copy everything between `<style>` tags (lines 7-157)
3. Create new file `public/styles.css`
4. Paste the copied CSS into `styles.css`
5. In `index.html`, replace the `<style>` block with:
   ```html
   <link rel="stylesheet" href="styles.css">
   ```
6. Test: Run local server and verify page looks identical

```bash
# From repo root
python3 -m uvicorn app.main:app --reload
# Visit http://localhost:8000/
```

---

### Step 2: Apply Arrested Development Color Palette

**Goal**: Replace current purple/blue colors with orange theme

**In `public/styles.css`:**

1. **Add CSS custom properties** at the top of the file:
   ```css
   :root {
     /* Arrested Development brand colors */
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

2. **Update body background gradient**:
   ```css
   body {
     background: linear-gradient(135deg, #FF6B35 0%, #F7931E 100%);
     /* OR for striped pattern (optional): */
     background: repeating-linear-gradient(
       45deg,
       #FF6B35,
       #FF6B35 20px,
       #FFFFFF 20px,
       #FFFFFF 40px
     );
   }
   ```

3. **Update heading colors**:
   ```css
   h1 {
     color: var(--color-orange);
   }

   h2 {
     color: var(--color-text-dark);
     border-bottom: 2px solid var(--color-orange);
   }

   h3 {
     color: var(--color-orange);
   }
   ```

4. **Update accent colors**:
   ```css
   .endpoint {
     border-left: 4px solid var(--color-orange);
   }

   .footer a {
     color: var(--color-orange);
   }
   ```

5. **Test contrast ratios**: Use WebAIM Contrast Checker
   - Orange `#FF6B35` on white = 3.5:1 (OK for large text only)
   - Dark gray `#2C3E50` on white = 12.6:1 (OK for all text)

---

### Step 3: Enhance Visual Hierarchy

**Goal**: Make the page feel more professional and modern

**In `public/styles.css`:**

1. **Add subtle shadow to container**:
   ```css
   .container {
     box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
   }
   ```

2. **Improve endpoint block styling**:
   ```css
   .endpoint {
     background: var(--color-cream);
     border-left: 4px solid var(--color-orange);
     border-radius: 8px;
     transition: transform 0.2s ease;
   }

   .endpoint:hover {
     transform: translateX(4px);
   }
   ```

3. **Add orange accent to method badges**:
   ```css
   .method {
     background: var(--color-orange);
     color: white;
   }
   ```

4. **Polish the header**:
   ```css
   h1 {
     color: var(--color-orange);
     text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
   }
   ```

---

### Step 4: Responsive Design Improvements

**Goal**: Ensure mobile-first approach works on all screen sizes

**Add to `public/styles.css`:**

```css
/* Mobile (default, 320px+) - Already defined */

/* Tablet (600px+) */
@media (min-width: 600px) {
  .container {
    padding: 30px;
  }

  h1 {
    font-size: 2.75em;
  }
}

/* Desktop (900px+) */
@media (min-width: 900px) {
  .container {
    max-width: 900px;
    margin: 0 auto;
    padding: 50px;
  }

  h1 {
    font-size: 3em;
  }
}
```

**Test on multiple screen sizes**:
- Mobile: 320px, 375px, 414px
- Tablet: 768px, 834px
- Desktop: 1024px, 1440px, 1920px

---

### Step 5: Accessibility Validation

**Goal**: Ensure WCAG 2.1 Level AA compliance

1. **Contrast Ratio Checks**:
   - Visit https://webaim.org/resources/contrastchecker/
   - Test all text/background combinations:
     - Body text `#2C3E50` on white `#FFFFFF`: Should be 4.5:1+
     - Orange headers `#FF6B35` on white: Should be 3:1+ (large text)
     - Code text on dark bg: Should be 4.5:1+

2. **Semantic HTML Check**:
   ```html
   <!-- Verify heading hierarchy -->
   <h1> → <h2> → <h3>  ✅ Correct
   <h1> → <h3>          ❌ Skip level
   ```

3. **Keyboard Navigation**:
   - Press Tab key to navigate through links
   - All interactive elements should be focusable
   - Add focus styles if needed:
     ```css
     a:focus {
       outline: 2px solid var(--color-orange);
       outline-offset: 2px;
     }
     ```

4. **Browser DevTools Audit**:
   - Chrome: Open DevTools → Lighthouse → Accessibility
   - Should score 95+

---

### Step 6: Performance Validation

**Goal**: Ensure page loads quickly

1. **Check CSS file size**:
   ```bash
   ls -lh public/styles.css
   # Should be < 50KB
   ```

2. **Test page load time**:
   - Chrome DevTools → Network tab
   - Refresh page
   - DOMContentLoaded should be < 1 second
   - Load should be < 2 seconds

3. **Optimize if needed**:
   - Remove unused CSS rules
   - Minify whitespace (optional, not required for MVP)

---

### Step 7: Cross-Browser Testing

**Goal**: Verify consistent appearance across browsers

**Test in these browsers**:
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

**What to check**:
- ✅ Orange colors display correctly
- ✅ Layout doesn't break
- ✅ Fonts render consistently
- ✅ Responsive breakpoints work
- ✅ No JavaScript errors (page should work without JS)

---

## Testing Checklist

### Visual Testing
- [ ] Page loads with orange theme
- [ ] All endpoint blocks have orange left border
- [ ] Headers use orange color
- [ ] Code examples have dark background
- [ ] Footer links are orange
- [ ] Responsive layout works on mobile, tablet, desktop

### Accessibility Testing
- [ ] All text/background combinations pass contrast checker
- [ ] Heading hierarchy is correct (H1 → H2 → H3)
- [ ] Links are keyboard-navigable
- [ ] Focus indicators are visible
- [ ] DevTools Accessibility audit passes (95+ score)

### Performance Testing
- [ ] CSS file size < 50KB
- [ ] Page loads in < 2 seconds
- [ ] No external font requests
- [ ] First Contentful Paint < 1 second

### Browser Testing
- [ ] Chrome: Renders correctly
- [ ] Firefox: Renders correctly
- [ ] Safari: Renders correctly
- [ ] Edge: Renders correctly

### Content Preservation
- [ ] All endpoint documentation is present
- [ ] Code examples are readable and copyable
- [ ] Error messages section is visible
- [ ] Footer links work
- [ ] No content was removed during redesign

---

## Troubleshooting

### Issue: CSS file not loading

**Symptoms**: Page shows unstyled HTML

**Solutions**:
1. Check the `<link>` tag in `index.html`:
   ```html
   <link rel="stylesheet" href="styles.css">
   ```
2. Verify `styles.css` is in the `public/` directory
3. Check browser console for 404 errors
4. Clear browser cache and hard refresh (Cmd+Shift+R / Ctrl+Shift+R)

---

### Issue: Colors don't match promotional images

**Solution**: Use color picker tool to extract exact colors from `etc/art-examples/download.jpeg`:
- Main orange: `#FF6B35`
- Alternate: `#F7931E`

---

### Issue: Contrast ratio fails

**Symptoms**: WebAIM checker shows ratio < 4.5:1 for normal text

**Solutions**:
- Use orange `#FF6B35` ONLY for large text (18pt+)
- Use dark gray `#2C3E50` for body text
- Never use light orange for small text on white

---

### Issue: Page looks broken on mobile

**Symptoms**: Text overflows, buttons too small, layout squished

**Solutions**:
1. Check viewport meta tag exists:
   ```html
   <meta name="viewport" content="width=device-width, initial-scale=1.0">
   ```
2. Verify mobile-first CSS is at the top (no media query)
3. Test responsive breakpoints activate at correct widths

---

## Deployment

Once all testing passes:

1. **Commit changes**:
   ```bash
   git add public/index.html public/styles.css
   git commit -m "Redesign index page with Arrested Development branding

   - Extract CSS to separate file for maintainability
   - Apply orange/white color palette from show's promotional materials
   - Ensure WCAG 2.1 Level AA accessibility compliance
   - Maintain responsive design across all screen sizes"
   ```

2. **Push to feature branch**:
   ```bash
   git push origin 006-index-styling
   ```

3. **Create pull request** for review

4. **After merge**: GitHub Actions will automatically deploy to Lambda

---

## Expected Outcome

After completing these steps, you should have:

✅ A visually distinctive API homepage with Arrested Development's orange branding
✅ CSS extracted to a separate `styles.css` file
✅ Full WCAG 2.1 Level AA accessibility compliance
✅ Responsive design working on all screen sizes (320px - 2560px)
✅ Professional appearance that maintains developer documentation clarity
✅ Page load time under 2 seconds

---

## Next Steps

- Run `/speckit.tasks` to generate detailed implementation tasks
- Begin implementation following the task breakdown
- Test continuously as you implement each change
- Request code review before merging to main
