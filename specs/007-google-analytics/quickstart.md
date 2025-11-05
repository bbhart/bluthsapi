# Quickstart: Google Analytics 4 Integration

**Feature**: 007-google-analytics
**Audience**: Developer implementing this feature
**Time to Implement**: ~15 minutes

## Overview

This guide walks through adding Google Analytics 4 tracking to the Bluths API website. The implementation requires modifying a single HTML file to add Google's standard gtag.js tracking snippet.

## Prerequisites

- [x] Google Analytics account with measurement ID: `G-PEMHDLKW9H` (already created)
- [x] Access to the repository on branch `007-google-analytics`
- [x] Local development environment with Python 3.11+ and FastAPI
- [x] Web browser with DevTools for testing

## Implementation Steps

### Step 1: Modify index.html

**File**: `public/index.html`

**Action**: Add GA4 tracking snippet in the `<head>` section, after `<meta>` tags and before `<link>` stylesheets.

**Insert this code**:

```html
    <!-- Google Analytics 4 -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-PEMHDLKW9H"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-PEMHDLKW9H');
    </script>
```

**Complete `<head>` section should look like**:

```html
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Arrested Development Quotes API</title>

    <!-- Google Analytics 4 -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-PEMHDLKW9H"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-PEMHDLKW9H');
    </script>

    <link rel="stylesheet" href="styles.css">
</head>
```

**Note**: This is the only code change required. No Python files, no config files, no deployment changes.

### Step 2: Test Locally

**Start the development server**:
```bash
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Open the site** in your browser:
```
http://localhost:8000
```

**Verify analytics script loads**:

1. Open Browser DevTools (F12 or right-click → Inspect)
2. Go to **Network** tab
3. Reload the page
4. Filter by "google" or "analytics"
5. Confirm you see requests to:
   - `googletagmanager.com/gtag/js?id=G-PEMHDLKW9H` (status 200)
   - `google-analytics.com/g/collect?...` (status 200 or 204)

**Expected behavior**:
- Page loads normally
- Two network requests to Google domains succeed
- No console errors
- Site functionality unchanged

### Step 3: Test Graceful Degradation

**Test with ad blocker**:

1. Install uBlock Origin, Privacy Badger, or similar extension
2. Enable the ad blocker
3. Reload `http://localhost:8000`
4. Verify:
   - Page loads without errors
   - No console warnings
   - Site functionality works normally
   - Analytics requests blocked (visible in Network tab with strikethrough or red icon)

**Expected behavior**: Site continues to work perfectly even when analytics is blocked.

### Step 4: Verify Real-Time Tracking (Optional)

**If you have access to the Google Analytics dashboard**:

1. Go to [Google Analytics](https://analytics.google.com/)
2. Select the property for `G-PEMHDLKW9H`
3. Navigate to: **Reports → Realtime**
4. In another browser window, visit `http://localhost:8000`
5. Within 10-30 seconds, verify:
   - "1 user right now" appears in Realtime dashboard
   - Page view event shows with path `/`
   - Location, device, and browser data visible

**Note**: Realtime reports may take up to 1 minute to update. If you don't see data immediately, wait 60 seconds and refresh the dashboard.

## Deployment

### Option 1: Deploy via Git + GitHub Actions (Recommended)

```bash
# Commit the change
git add public/index.html
git commit -m "Add Google Analytics 4 tracking

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to remote
git push origin 007-google-analytics

# Create pull request or merge to main
# GitHub Actions will automatically deploy to AWS Lambda
```

### Option 2: Deploy via SAM CLI (Manual)

```bash
# Build the application
cd deploy/sam
sam build --use-container

# Deploy to AWS
sam deploy --stack-name bluths-api --resolve-s3

# Verify deployment
curl https://your-api-gateway-url.execute-api.region.amazonaws.com/prod/health
```

**Note**: The `public/` directory is automatically included in the Lambda deployment package, so no SAM template changes are needed.

## Verification Checklist

After deployment to production:

- [ ] Visit production site in browser
- [ ] Check browser DevTools Network tab for successful GA requests
- [ ] Wait 24-48 hours for full reports to populate
- [ ] Verify in Google Analytics dashboard:
  - [ ] **Realtime** → See current visitors
  - [ ] **Engagement → Pages and screens** → Verify page views for `/`
  - [ ] **Acquisition → Traffic acquisition** → Verify referral sources (direct, google, etc.)
  - [ ] **User attributes → Demographics** → Verify location and device data

## Troubleshooting

### Problem: No analytics requests in Network tab

**Possible causes**:
1. Ad blocker is active → Expected behavior (site should still work)
2. Typo in measurement ID → Verify `G-PEMHDLKW9H` exactly
3. Script not loading → Check placement in `<head>` section

**Fix**: Review Step 1, ensure code is copied exactly as shown

### Problem: Console errors mentioning "gtag" or "dataLayer"

**Possible cause**: Script syntax error or missing dependency

**Fix**:
1. Clear browser cache
2. Verify both `<script>` tags are present (async gtag.js loader + inline config)
3. Ensure no extra quotes or brackets in the snippet

### Problem: No data in Google Analytics dashboard after 48 hours

**Possible causes**:
1. Wrong measurement ID → Verify `G-PEMHDLKW9H`
2. GA property not configured → Contact site owner for GA access
3. No traffic to production site → Generate some test visits

**Fix**:
1. Verify Realtime reports first (immediate feedback)
2. Check GA property settings (Admin → Property → Data Streams)
3. Generate test traffic from multiple devices/locations

### Problem: Page load time increased significantly

**Unlikely, but if it occurs**:

**Measure actual impact**:
```bash
# Use browser DevTools Performance tab
# Record page load
# Check for blocking scripts in the waterfall
```

**Expected**: gtag.js loads asynchronously (~100-300ms first visit, ~10ms cached) without blocking page render

**If blocking occurs**: Verify `async` attribute is present on the gtag.js `<script>` tag

## Performance Validation

**Baseline** (before GA4):
```bash
# Measure page load time
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000
```

**With GA4** (after implementation):
```bash
# Measure again, compare results
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000
```

**Expected**: Difference < 100ms (success criteria: SC-003)

**For curl-format.txt**:
```
time_namelookup:  %{time_namelookup}s\n
time_connect:     %{time_connect}s\n
time_starttransfer: %{time_starttransfer}s\n
time_total:       %{time_total}s\n
```

## Next Steps

After successful implementation:

1. Monitor Google Analytics for 7-14 days
2. Review traffic patterns, popular pages, referral sources
3. Evaluate if custom event tracking is needed (future enhancement)
4. Document any privacy policy updates (site owner responsibility)

## Success Criteria Validation

From `spec.md`, verify these criteria are met:

- [x] **SC-001**: Analytics data appears in GA dashboard within 48 hours
- [x] **SC-002**: 95%+ page views tracked (allow 5% for ad blockers)
- [x] **SC-003**: Page load time impact < 100ms
- [x] **SC-004**: All metrics visible (traffic, demographics, referrals)
- [x] **SC-005**: Site functions normally with blocked analytics

## Resources

- [Research Document](./research.md) - Technical details and best practices
- [Feature Spec](./spec.md) - Requirements and acceptance criteria
- [Implementation Plan](./plan.md) - Architecture and design decisions
- [Google Analytics Setup Guide](https://support.google.com/analytics/answer/9304153)

## Summary

**Total Changes**: 1 file modified (`public/index.html`)
**Lines of Code**: ~10 lines added
**Testing Time**: ~5 minutes
**Deployment**: Automatic via existing pipeline

This is a low-risk, high-value change that adds analytics visibility without impacting site performance or user experience.
