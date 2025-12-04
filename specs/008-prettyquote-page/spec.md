# Feature Specification: Pretty Quote Display Page

**Feature Branch**: `008-prettyquote-page`
**Created**: 2025-12-03
**Status**: Draft
**Input**: User description: "Create a new html page called prettyquote.html. It should fetch a random quote using the random endpoint and then display it on this webpage. Only display the quote text, not the other fields. Make it large enough so it consumes about half the page so that it's easy to copy to clipboard on a mobile phone. Do not link to this page from the index page or mention its existence."

## Clarifications

### Session 2025-12-03

- Q: Should there be a dedicated Copy button? → A: Yes, add a Copy button at the bottom of the page, centered, that copies the quote text to clipboard.
- Q: Should the Copy button show visual feedback on success? → A: Yes, show brief visual feedback (button text changes to "Copied!" for 1-2 seconds).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Random Quote on Mobile (Priority: P1)

A user visits the prettyquote.html page on their mobile phone to quickly see a random Arrested Development quote displayed prominently, making it easy to read and copy to share with friends.

**Why this priority**: This is the core and only functionality of the page - displaying a quote in a mobile-friendly, easy-to-copy format.

**Independent Test**: Can be fully tested by visiting the page on a mobile device, verifying a quote appears large and centered, and successfully copying the quote text to clipboard.

**Acceptance Scenarios**:

1. **Given** a user navigates to prettyquote.html on any device, **When** the page loads, **Then** a random quote is fetched from the API and displayed as text only (no ID, speaker, or other metadata).
2. **Given** the quote is displayed, **When** the user views the page on a mobile phone, **Then** the quote text consumes approximately half the vertical viewport and is large enough to read comfortably.
3. **Given** the quote is displayed, **When** the user taps the Copy button at the bottom of the page, **Then** the quote text is copied to their clipboard and the button shows "Copied!" feedback for 1-2 seconds.
4. **Given** the quote is displayed on mobile, **When** the user long-presses on the quote text, **Then** they can also select and copy the entire quote manually.

---

### User Story 2 - Refresh for New Quote (Priority: P2)

A user wants to see a different quote and refreshes the page to get another random quote.

**Why this priority**: Secondary functionality that enhances usability once the primary display works.

**Independent Test**: Can be tested by refreshing the page multiple times and verifying different quotes appear.

**Acceptance Scenarios**:

1. **Given** a user is viewing a quote on prettyquote.html, **When** they refresh the page, **Then** a new random quote is fetched and displayed.

---

### Edge Cases

- What happens when the API is unavailable or returns an error? The page displays a user-friendly error message.
- What happens if the quote text is very long? The text remains readable with appropriate sizing and does not overflow the viewport.
- What happens if the quote text is very short? The text is still displayed prominently and centered.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST serve a static HTML page at the path `/prettyquote.html` (in the public directory alongside index.html).
- **FR-002**: The page MUST fetch a random quote from the existing `/api/quotes/random` endpoint when loaded.
- **FR-003**: The page MUST display ONLY the quote text - no ID, speaker name, context, or other metadata.
- **FR-004**: The quote text MUST be displayed in a large font size that consumes approximately 50% of the vertical viewport height.
- **FR-005**: The quote text MUST be centered both horizontally and vertically on the page.
- **FR-006**: The page MUST be responsive and optimized for mobile phone viewing.
- **FR-007**: The quote text MUST be easily selectable for copying to clipboard on mobile devices.
- **FR-008**: The page MUST display a Copy button at the bottom of the page, centered horizontally.
- **FR-009**: The Copy button MUST copy the quote text to the user's clipboard when tapped.
- **FR-010**: The Copy button MUST display visual feedback ("Copied!") for 1-2 seconds after successful copy.
- **FR-011**: The page MUST NOT be linked from index.html or any other page in the application.
- **FR-012**: The page MUST NOT be mentioned in any public documentation.
- **FR-013**: The page MUST display a user-friendly error message if the API request fails.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can view a random quote on the page within 2 seconds of page load on a standard mobile connection.
- **SC-002**: Quote text occupies approximately 50% of the vertical viewport on mobile devices (320px - 768px width).
- **SC-003**: Users can successfully copy quote text to clipboard using the Copy button on first attempt on both iOS and Android devices.
- **SC-004**: The page loads and displays correctly on all modern mobile browsers (Safari, Chrome, Firefox).
- **SC-005**: The Copy button is visible and accessible at the bottom of the viewport on mobile devices.
- **SC-006**: Page remains undiscoverable through normal navigation - no links exist to it from other pages.

## Assumptions

- The existing `/api/quotes/random` endpoint is reliable and will continue to return the current JSON structure (`data.quote`).
- The page will be served as a static file by the existing static file serving mechanism from the `public/` directory.
- Users accessing this page have the direct URL (it is intentionally unlisted).
- Mobile devices have standard text selection and copy functionality available.
- The design should be minimal/clean to focus attention on the quote text.
