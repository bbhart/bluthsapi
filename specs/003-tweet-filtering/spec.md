# Feature Specification: Smart Tweet Staging Filter

**Feature Branch**: `003-tweet-filtering`
**Created**: 2025-10-27
**Status**: Draft
**Input**: User description: "Smarter filtering of the tweets_staging.json file. I will provide criteria in the spec."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Filter Low-Quality Tweets (Priority: P1)

As a content curator, I need to automatically filter out low-quality tweets from the staging file so that only high-quality content moves forward to the quote conversion process.

**Why this priority**: This is the core filtering capability that directly impacts content quality. Removing low-quality content early in the pipeline saves manual review time and improves the overall quality of published quotes.

**Independent Test**: Can be fully tested by running the filter on a staging file with known low-quality tweets and verifying they are removed based on defined quality criteria. Delivers value by reducing manual curation workload and improving content quality.

**Acceptance Scenarios**:

1. **Given** a staging file with tweets below minimum engagement thresholds, **When** the filter is applied, **Then** tweets with low favorite_count and retweet_count are removed from the staging file
2. **Given** a staging file with tweets containing only hashtags or @mentions, **When** the filter is applied, **Then** those tweets are removed as non-substantive content
3. **Given** a staging file with tweets containing hashtags, **When** the filter is applied, **Then** those tweets are removed regardless of their engagement metrics
4. **Given** a staging file with tweets marked as retweets, **When** the filter is applied, **Then** all retweets are removed
5. **Given** a staging file with tweets below engagement thresholds (< 100 favorites and < 5 retweets), **When** the filter is applied, **Then** those tweets are removed

---

### User Story 2 - Preserve High-Value Content (Priority: P2)

As a content curator, I want to ensure that tweets meeting quality thresholds are retained even if they have characteristics that might otherwise exclude them, so that valuable content is not lost.

**Why this priority**: This prevents over-filtering and ensures the system is balanced - removing noise while preserving valuable content. It's a refinement of the basic filtering logic.

**Independent Test**: Can be tested by running the filter on staging data with high-engagement tweets that have borderline characteristics and verifying they are retained. Delivers value by ensuring quality content isn't accidentally filtered out.

**Acceptance Scenarios**:

1. **Given** a staging file with tweets that have high engagement (favorite_count >= 100 OR retweet_count >= 5), **When** the filter is applied, **Then** the tweet is retained as long as it doesn't contain hashtags or is a retweet
2. **Given** a staging file with tweets from different date ranges, **When** the filter is applied, **Then** tweets are not penalized based on date alone (older tweets may have lower engagement)
3. **Given** a staging file with tweets containing media attachments, **When** the filter is applied, **Then** tweets with media are given preferential treatment in borderline cases

---

### User Story 3 - Remove Near-Duplicate Tweets (Priority: P3)

As a content curator, I need to automatically detect and remove tweets that are materially similar to previously retained tweets so that only unique content moves forward to the quote conversion process.

**Why this priority**: Deduplication improves content quality but is less critical than basic filtering. The filter provides value even without deduplication, but removing near-duplicates reduces manual review effort and improves the final dataset quality.

**Independent Test**: Can be tested by running the filter on a staging file with known near-duplicate tweets and verifying that similar tweets are removed while keeping the first occurrence. Delivers value by eliminating redundant content variations.

**Acceptance Scenarios**:

1. **Given** a staging file with multiple tweets containing the same core message with minor variations, **When** the similarity filter is applied, **Then** the first tweet is retained and subsequent similar tweets are removed
2. **Given** tweets with different wording but same meaning (e.g., "I've made a huge mistake" vs "I have made a huge mistake"), **When** the similarity filter is applied, **Then** they are identified as duplicates and only one is retained
3. **Given** tweets that are completely different in content, **When** the similarity filter is applied, **Then** all tweets are retained (no false positives)
4. **Given** duplicate tweets being removed, **When** the filter completes, **Then** five example comparisons are displayed showing a kept tweet and its removed similar tweets for human validation of the similarity threshold
5. **Given** tweets with punctuation or capitalization differences but identical content, **When** the similarity filter is applied, **Then** they are identified as duplicates

---

### User Story 4 - Generate Filter Report (Priority: P4)

As a content curator, I need to see a summary report after filtering showing what was removed and why, so that I can validate the filtering logic and adjust criteria if needed.

**Why this priority**: Transparency and validation are important but not critical for the core filtering functionality. The filter can work without reporting, but reporting improves trust and allows tuning.

**Independent Test**: Can be tested by running the filter and verifying that a report file or output shows counts of removed tweets by reason category. Delivers value by providing visibility into filtering decisions.

**Acceptance Scenarios**:

1. **Given** a staging file that has been filtered, **When** the filter completes, **Then** a report is generated showing total tweets processed, retained, and removed
2. **Given** tweets removed for various reasons, **When** the report is generated, **Then** removal reasons are categorized (e.g., "low engagement", "contains hashtags", "retweet", "no substantive content", "duplicate/similar")
3. **Given** a generated filter report, **When** I review it, **Then** each category shows the count of tweets removed for that reason
4. **Given** a filter operation that removes tweets, **When** the report is generated, **Then** specific tweet IDs are listed for each removal category for audit purposes

---

### Edge Cases

- What happens when all tweets in the staging file fail quality criteria? (System should generate an empty output file and warn in the report)
- How does the system handle tweets with missing metadata fields (e.g., no favorite_count)? (Treat missing numeric fields as zero; missing text fields as empty string)
- What happens if the staging file is malformed or invalid JSON? (Filter script should fail with a clear error message before attempting to process)
- How are tweets with exactly the threshold value handled? (Use inclusive thresholds - a tweet meeting the exact threshold is retained)
- What if a tweet has high favorites but zero retweets (or vice versa)? (Composite scoring considers both metrics, allowing one strong metric to compensate for a weak one)
- What happens when primarySpeaker field is empty? (This should not affect filtering - speaker attribution happens after filtering)
- How does the filter handle Unicode characters, emojis, and special characters in text length calculations? (Character count is based on actual characters, not bytes)
- What if a tweet contains hashtags but has exceptionally high engagement? (Hashtag exclusion takes precedence - tweets with hashtags are always removed regardless of engagement)
- What if a tweet mentions a hashtag in quoted text but doesn't contain an actual "#" symbol? (Text content is checked literally for "#" symbol - if no "#" present, tweet is not filtered for hashtags)
- How are near-duplicates identified when tweets have minor differences? (Use text similarity algorithm to compare normalized text - punctuation, capitalization, and whitespace differences are ignored)
- What happens when multiple tweets are all similar to each other? (The first tweet in the file is retained, all subsequent similar tweets are removed)
- How similar do tweets need to be to be considered duplicates? (Similarity threshold is configurable; default should be tuned to avoid false positives while catching true near-duplicates)
- What if two tweets share some words but have different meanings? (Similarity algorithm should consider word order and context, not just shared words)
- How does deduplication interact with engagement filtering? (Engagement filtering happens first, then deduplication runs on the remaining tweets)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST remove tweets marked as retweets (is_retweet: true) from the staging file
- **FR-002**: System MUST remove tweets with engagement metrics below defined minimums (favorite_count < 100 OR retweet_count < 5)
- **FR-003**: System MUST use composite scoring that considers both favorite_count and retweet_count together, allowing strong performance in one metric to compensate for weakness in another
- **FR-004**: System MUST remove tweets consisting only of hashtags, @mentions, or URLs with no substantive text content
- **FR-005**: System MUST remove any tweets containing hashtags (any "#" symbol in the text)
- **FR-006**: System MUST detect and remove near-duplicate tweets using a text similarity algorithm that compares tweet content after normalization
- **FR-007**: System MUST normalize tweet text for similarity comparison by removing punctuation, converting to lowercase, and collapsing whitespace
- **FR-008**: System MUST retain the first occurrence of a tweet when duplicates are found and remove all subsequent similar tweets
- **FR-009**: System MUST output five examples of similarity comparisons to standard output, each showing a retained tweet and the similar tweets that were removed, to allow human validation of the similarity threshold
- **FR-010**: System MUST allow the similarity threshold to be configurable through a configuration file or command-line parameter
- **FR-011**: System MUST preserve tweets with media attachments (non-empty media_urls array) even if they are borderline on other criteria
- **FR-012**: System MUST handle missing or null metadata fields gracefully by treating them as zero (for numeric fields) or empty string (for text fields)
- **FR-013**: System MUST maintain the original staging file structure and metadata in the filtered output
- **FR-014**: System MUST generate a filter report showing counts and categorization of removed tweets
- **FR-015**: System MUST allow configuration of all filtering thresholds and criteria through a configuration file or command-line parameters
- **FR-016**: System MUST preserve the order of tweets in the staging file after filtering
- **FR-017**: System MUST apply engagement and quality filters before deduplication, so that duplicate detection only runs on tweets that have already passed other filters

### Key Entities

- **FilteredTweet**: A tweet from the staging file that has passed all quality criteria and will be included in the filtered output. Contains all original metadata (tweet_id, text, created_at, favorite_count, retweet_count, media_urls, primarySpeaker).
- **FilterCriteria**: A set of configurable rules defining minimum quality thresholds including minimum engagement metrics (100 favorites OR 5 retweets), hashtag exclusion rules, similarity threshold for duplicate detection, and rules for handling media-attached tweets.
- **FilterReport**: A summary of filtering results including total tweets processed, count of tweets retained, count of tweets removed by category (retweets, low engagement, contains hashtags, near-duplicate, no substantive content), and lists of specific tweet IDs removed for each reason.
- **SimilarityComparison**: An example output showing one retained tweet and one or more removed tweets that were identified as similar, used to demonstrate the similarity algorithm's behavior for human validation. Five of these comparisons are output to standard output during each filter run.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Filtered staging file contains at least 70% fewer low-quality tweets (those with engagement below threshold) compared to the unfiltered file
- **SC-002**: Content curator can review and approve filtered staging file in under 30 minutes (compared to 2+ hours for unfiltered data)
- **SC-003**: Filter processing completes in under 10 seconds for a staging file containing 5,000 tweets (allowing for similarity computation overhead)
- **SC-004**: Zero high-quality tweets (those with engagement above 2x the threshold) are accidentally removed by the engagement or hashtag filters
- **SC-005**: Similarity algorithm achieves less than 5% false positive rate (removing tweets that are not actually duplicates) based on human review of the five example comparisons
- **SC-006**: Similarity algorithm successfully identifies and removes at least 80% of true near-duplicate tweets
- **SC-007**: Filter report provides sufficient detail for curator to validate filtering decisions without manually reviewing removed tweets

## Scope *(mandatory)*

### In Scope

- Automated filtering of tweets_staging.json based on quality criteria
- Configurable filtering thresholds and rules
- Near-duplicate detection using text similarity algorithm
- Output of five example similarity comparisons to standard output for human validation
- Generation of filtered staging file maintaining original structure
- Filter reporting showing removal statistics and reasons (including duplicate count)
- Handling of edge cases (missing data, malformed entries)
- Preservation of high-value content with special rules for media attachments

### Out of Scope

- Manual review interface or web UI for filtering decisions (this remains a file-based operation)
- Machine learning or AI-based content quality assessment beyond basic text similarity
- Semantic similarity or meaning-based duplicate detection (using simple text comparison only)
- Speaker attribution or primarySpeaker field population (handled in separate feature)
- Image content analysis or media quality assessment
- Natural language processing for sentiment or topic analysis
- Integration with Twitter/X API for fetching additional metadata
- Conversion to final quotes.json format (handled by existing feature 002)
- Cross-language duplicate detection (assumes all content is in English)

## Assumptions *(mandatory)*

- The tweets_staging.json file follows the structure established in feature 002-tweet-to-quote-conversion
- Engagement metrics (favorite_count, retweet_count) are reliable indicators of content quality
- Content curator has the ability to adjust filtering criteria through configuration if initial thresholds are too aggressive or too lenient
- The staging file fits in memory (reasonable for files up to several thousand tweets)
- Text content is in English (for any pattern matching or excluded term detection)
- The filter operates as a pre-processing step before manual review, not as a replacement for human judgment

## Dependencies *(mandatory)*

- Feature 002-tweet-to-quote-conversion must be complete, as this feature operates on the tweets_staging.json file created by that feature
- The tweets_staging.json file must exist and contain valid JSON before filtering can occur
