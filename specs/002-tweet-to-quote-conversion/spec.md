# Feature Specification: Tweet to Quote Conversion System

**Feature Branch**: `002-tweet-to-quote-conversion`
**Created**: 2025-10-24
**Status**: Draft
**Input**: User description: "Propose a solution for converting @etc/tweets.js to @app/data/quotes.json, with a step during the conversion so that a human may review a file and remove or edit some records before converting. The solution should also create a script that will allow for downloading all of the media referenced in media_url_https into a dedicated folder so that the images can be transferred to the S3 bucket."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Extract Quotes from Tweet Archive (Priority: P1)

As a content curator, I need to convert historical tweet data into a structured quote format so that the quotes can be used in the application.

**Why this priority**: This is the foundational conversion that all other functionality depends on. Without extracting the quote data, there's nothing to review or enhance with media.

**Independent Test**: Can be fully tested by running the extraction script on a sample tweet file and verifying that quotes with all required fields are extracted to a staging file. Delivers value by making tweet content available for review.

**Acceptance Scenarios**:

1. **Given** a tweets.js file with multiple tweet objects, **When** the extraction script is run, **Then** a staging file is created containing all tweets with their text content, creation date, and unique identifiers
2. **Given** a tweet with only a URL and no text, **When** the extraction script processes it, **Then** that tweet is excluded from the staging file (not a viable quote)
3. **Given** a tweet that is a retweet (starts with "RT @"), **When** the extraction script processes it, **Then** that tweet is marked with a retweet flag in the staging file and will be excluded from final conversion
4. **Given** tweets with special characters or emojis, **When** the extraction script processes them, **Then** the text is preserved exactly as written
5. **Given** a tweet starting with "Michael: I've made a huge mistake", **When** the extraction script processes it, **Then** "Michael" is identified as a potential speaker in the staging metadata

---

### User Story 2 - Review and Edit Extracted Quotes (Priority: P2)

As a content curator, I need to review the extracted quotes in a human-readable format and remove or edit records before final conversion, so that only appropriate and accurate quotes are published.

**Why this priority**: Human review ensures quality and appropriateness of content. This step allows filtering out retweets, low-quality tweets, or content that shouldn't be published as quotes.

**Independent Test**: Can be tested by manually editing the staging file (removing entries, modifying text) and verifying that subsequent conversion respects those changes. Delivers value by providing quality control.

**Acceptance Scenarios**:

1. **Given** a staging file with extracted tweet data, **When** I open it for review, **Then** I can easily read each tweet's content, see its metadata, and identify which tweets to keep or remove
2. **Given** a staging file entry that I want to remove, **When** I delete that entry from the file, **Then** it is excluded from the final quotes.json output
3. **Given** a staging file entry with text I want to modify, **When** I edit the text content, **Then** the modified text appears in the final quotes.json output
4. **Given** a staging file with metadata fields, **When** I review entries, **Then** I can see the original tweet ID, date, speaker information, and media references for context

---

### User Story 3 - Convert Reviewed Quotes to Final Format (Priority: P3)

As a content curator, I need to convert the reviewed staging file into the final quotes.json format used by the application, so that the quotes can be loaded into the system.

**Why this priority**: This completes the conversion pipeline after review. It's the final transformation step but depends on the previous two steps being complete.

**Independent Test**: Can be tested by running the conversion script on a reviewed staging file and verifying the output matches the quotes.json schema with proper quote IDs, speakers, and text fields. Delivers value by making quotes application-ready.

**Acceptance Scenarios**:

1. **Given** a reviewed staging file, **When** the conversion script is run, **Then** a quotes.json file is created with the correct schema structure (id, quote, primarySpeaker, imageUrl fields)
2. **Given** staging entries with associated image media, **When** the conversion script runs, **Then** the imageUrl field contains the first image URL from the tweet
3. **Given** a staging entry with text "Lucille: I don't understand the question, and I won't respond to it", **When** the conversion script processes it, **Then** primarySpeaker is set to "Lucille" and quote text is "I don't understand the question, and I won't respond to it"
4. **Given** existing quotes in quotes.json, **When** the conversion script runs, **Then** new quotes are appended without overwriting existing entries
5. **Given** tweets from the same speaker, **When** the conversion script runs, **Then** the primarySpeaker field is normalized consistently

---

### User Story 4 - Download Tweet Image Assets (Priority: P4)

As a content curator, I need to download all images referenced in tweets to a local folder, so that I can review them and upload them to the S3 bucket.

**Why this priority**: Media enhancement is valuable but not essential for basic quote functionality. Quotes work without media, making this a lower-priority enhancement.

**Independent Test**: Can be tested by running the media download script and verifying that all images from media_url_https fields are downloaded to the designated folder with proper naming. Delivers value by gathering image assets for potential use.

**Acceptance Scenarios**:

1. **Given** tweets with image media_url_https references, **When** the media download script is run, **Then** all images are downloaded to the specified media folder
2. **Given** tweets with video or animated GIF media, **When** the media download script processes them, **Then** those media items are skipped (only static images are downloaded)
3. **Given** a downloaded image, **When** I inspect the file, **Then** the filename corresponds to the tweet ID or media ID for easy identification
4. **Given** tweets with multiple images, **When** the media download script runs, **Then** all images from that tweet are downloaded with sequential numbering
5. **Given** a media URL that returns an error, **When** the download script processes it, **Then** the error is logged but the script continues processing remaining media
6. **Given** already-downloaded image files, **When** the script runs again, **Then** existing files are skipped to avoid redundant downloads

---

### Edge Cases

- What happens when a tweet has no full_text field? (System should skip or use empty string)
- How does the system handle tweets with only media and no text content? (Should be excluded as non-viable quotes)
- What happens if the staging file is corrupted or has invalid JSON? (Conversion script should fail with clear error message)
- How are duplicate tweets handled? (System should detect and consolidate duplicates based on tweet ID)
- What happens if image URLs return 404 or are no longer available? (Download script logs the failure and continues)
- How does the system handle tweets with @mentions in the text? (Text is preserved as-is, including @mentions)
- What happens if the quotes.json file already has a quote with the same ID? (System should auto-increment to the next available ID and continue)
- What if text starts with "GOB:" vs "Gob:" vs "G.O.B.:"? (System should preserve exact capitalization and punctuation from source text for primarySpeaker)
- What if a tweet has both images and videos? (Only images are extracted and downloaded; videos are skipped)
- What if the speaker name contains numbers (e.g., "George Michael:")? (Pattern matches alphabetical characters and spaces only; "George Michael" would match but "R2D2" would not)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST extract all tweets from the source tweets.js file that contain meaningful text content (non-empty full_text field)
- **FR-002**: System MUST create a staging file in a human-readable format (JSON or similar) that contains extracted tweet data with metadata
- **FR-003**: System MUST preserve tweet text exactly as written, including special characters, emojis, URLs, and formatting
- **FR-004**: System MUST identify and flag retweets (tweets starting with "RT @") in the staging file, and automatically exclude them from the final quotes.json output
- **FR-005**: System MUST extract and include tweet metadata: tweet ID, creation date, favorite count, retweet count, and speaker information
- **FR-006**: System MUST support manual editing of the staging file, allowing users to remove entries, modify text, and adjust metadata
- **FR-007**: System MUST convert the reviewed staging file into the target quotes.json format with proper schema (id, quote, primarySpeaker, imageUrl fields), where primarySpeaker is extracted from text if it starts with an alphabetical name followed by colon (e.g., "Michael:", "George Michael:"), otherwise set to empty string or null, and imageUrl contains the image URL if image media exists
- **FR-008**: System MUST generate unique quote IDs in the format "quote-N" where N is an incrementing number (no zero-padding) starting from the highest existing quote ID + 1 (or 1 if quotes.json is empty); if a collision is detected, auto-increment to the next available ID
- **FR-009**: System MUST append new quotes to existing quotes.json file without overwriting existing entries
- **FR-010**: System MUST extract image URLs (media_url_https) from tweet entities and extended_entities fields, filtering to include only photo type media; when multiple images exist, all URLs are stored in staging file, but only the first image URL is used for the final quotes.json imageUrl field
- **FR-011**: System MUST download only image files (photo type) referenced in media_url_https to a designated media folder, skipping videos and animated GIFs
- **FR-012**: System MUST name downloaded image files with identifiable names (tweet ID + media index or original media ID)
- **FR-013**: System MUST handle download failures gracefully by logging errors and continuing with remaining media
- **FR-014**: System MUST skip already-downloaded media files to avoid redundant downloads
- **FR-015**: System MUST provide clear progress feedback during extraction, conversion, and download operations

### Key Entities

- **Tweet Record**: Represents a single tweet from the source data, containing text content (full_text), metadata (id_str, created_at, favorite_count, retweet_count), speaker information, and media references (entities.media, extended_entities.media)
- **Staging Entry**: An intermediate format containing extracted tweet data in a human-editable structure, including all relevant fields needed for review and conversion
- **Quote Record**: The final format matching the application schema, containing id (unique quote identifier), quote (the text content), primarySpeaker (speaker name), and optional imageUrl (URL to associated media)
- **Media Asset**: A downloadable image file (photo type only) referenced in tweet media fields, identified by media_url_https, with associated metadata (tweet ID, media ID, file type)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: User can review and edit the staging file using any text editor without requiring special tools
- **SC-002**: Conversion from staging to final quotes.json preserves 100% of manually edited content accurately
- **SC-003**: Media download script successfully downloads at least 95% of available image files (accounting for unavailable URLs)
- **SC-004**: All generated quote IDs are unique and follow the specified format without collisions
- **SC-005**: Downloaded media files are organized in a way that allows easy identification of which tweet they belong to
- **SC-006**: Tweets with speaker name prefix (e.g., "Michael:", "Lucille:") correctly extract speaker to primarySpeaker field

## Clarifications

### Session 2025-10-24

- Q: How should the system determine the primarySpeaker for each quote? → A: Extract from text if it starts with alphabetical name followed by colon (e.g., "Michael:", "Lucille:", "George Michael:"), otherwise leave empty/null
- Q: When appending to an existing quotes.json file, what number should the quote ID counter start from? → A: Start from the highest existing quote ID number + 1 (scan existing file first)
- Q: What should the system do if a quote ID collision occurs (same ID already exists)? → A: Auto-increment to next available ID and continue
- Q: How should media references be stored in the final quotes.json? → A: Media references should be a URL stored in the imageUrl field
- Q: Should flagged retweets be automatically excluded or left for curator to decide? → A: Automatically exclude all flagged retweets from the final quotes.json output

## Assumptions

- The source tweets.js file follows Twitter's standard archive format with window.YTD.tweets.part0 structure
- The primarySpeaker field will be auto-extracted if tweet text starts with a name pattern (letters/spaces followed by colon), otherwise left empty/null for manual curation
- The staging file format will be JSON for easy editing and validation
- Media downloads will be stored locally before S3 upload; S3 upload is a separate manual or automated process
- The system will append to quotes.json rather than replacing it, allowing incremental additions
- Media file types supported include static images only (JPEG, PNG); videos and animated GIFs are excluded
- Network connectivity is available for media downloads
- The user has write permissions for the target directories

## Dependencies

- Source data file: etc/tweets.js must exist and be readable
- Target data file: app/data/quotes.json must be accessible for appending
- Media storage folder must be created or the script must have permission to create it
- Network access for downloading images from pbs.twimg.com domain

## Out of Scope

- Automatic S3 upload of downloaded media (this is a separate operation)
- Real-time tweet fetching or API integration with Twitter/X
- Automated sentiment analysis or content classification
- Handling of Twitter Spaces audio content
- Video or animated GIF download and processing (images only)
- Advanced speaker identification beyond simple name-colon prefix pattern matching
- User authentication or access control for running scripts
- Web-based UI for reviewing staging files (review happens in text editor)
