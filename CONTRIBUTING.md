# Contributing to Arrested Development Quotes API

Thank you for your interest in contributing to the Arrested Development Quotes API! We appreciate contributions of all kinds, from bug fixes and documentation improvements to new features and quote additions. The **most helpful** right now would be fixes to the data file (`/app/data/quotes.json`), though. 

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Contributing Quotes](#contributing-quotes)
- [Character Names](#character-names)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Submitting Changes](#submitting-changes)
- [Questions?](#questions)

## Code of Conduct

This project follows a simple code of conduct: be respectful, constructive, and professional in all interactions. We're here to build something fun and useful together.

## How Can I Contribute?

### Reporting Bugs

If you find a bug, please open an issue with:
- A clear, descriptive title
- Steps to reproduce the problem
- Expected vs. actual behavior
- Your environment (OS, Python version, etc.)

### Suggesting Enhancements

We welcome feature suggestions! Please open an issue describing:
- The enhancement you'd like to see
- Why it would be useful
- Any implementation ideas you have

### Contributing Code

We accept pull requests for:
- Bug fixes
- New features
- Performance improvements
- Documentation updates
- Test coverage improvements

### Contributing Quotes

**We especially welcome contributions to the quotes database!** If you have favorite Arrested Development quotes to add or corrections to existing ones, please submit a pull request updating `app/data/quotes.json`. See [Contributing Quotes](#contributing-quotes) below for details.

## Getting Started

### Prerequisites

- Python 3.11+ ([download](https://www.python.org/downloads/))
- uv package manager ([install](https://docs.astral.sh/uv/))
- Git
- Docker (optional - only needed if you want to test the containerized deployment locally)

### Setting Up Your Development Environment

1. **Fork and clone the repository**:
   ```bash
   git clone https://github.com/YOUR-USERNAME/bluthsapi.git
   cd bluthsapi
   ```

2. **Create a virtual environment and install dependencies**:
   ```bash
   # Create virtual environment with uv
   uv venv

   # Activate virtual environment
   # macOS/Linux:
   source .venv/bin/activate
   # Windows:
   .venv\Scripts\activate

   # Install production dependencies (FastAPI 0.115.0, etc.)
   uv pip install -r requirements.txt

   # Install development dependencies
   uv pip install -r requirements-dev.txt
   ```

3. **Configure environment variables**:
   ```bash
   # Copy example env file
   cp .env.example .env

   # Edit .env and set your S3_BASE_URL (optional for local development)
   nano .env
   ```

4. **Start the development server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Verify the setup**:
   ```bash
   # Test the API
   curl http://localhost:8000/api/quotes/random

   # View interactive docs
   open http://localhost:8000/docs
   ```

## Development Workflow

### Creating a Feature Branch

```bash
# Create a new branch from main
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

### Making Changes

1. Make your changes in the appropriate files
2. Test your changes locally
3. Run the test suite
4. Commit your changes with clear, descriptive messages

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/api/test_endpoints.py -v
```

### Testing Locally

```bash
# Test with uvicorn (hot reload)
uvicorn app.main:app --reload

# Test with Docker
docker build -t bluthsapi:test .
docker run -p 8000:8000 bluthsapi:test
```

## Contributing Quotes

The quotes database lives in `app/data/quotes.json`. It was populated haphazardly by scraping my old @bluthquotes tweets and 
trying to prune things down. 

I can definitely use help with filling out the `speakers` field. Roughly a third of
the quotes still have it empty, and some of the ones that are filled in are guesses
that may well be wrong. Corrections are as welcome as additions.

Additions and corrections via PR are most welcome!

### Quote Format

Each quote in the `quotes.json` file is an object in a flat array. The structure should follow:

```json
{
  "id": "quote-XXX",
  "quote": "The actual quote text here.",
  "speakers": "Character Name,Other Character",
  "context": "Season X, Episode Y - Episode Title",
  "imageUrl": "filename.jpg"
}
```

**Note:** The file contains a simple JSON array - add your quote directly to the array without any outer wrapper object.

**Required fields:**
- `id`: Unique identifier (see [ID Format Guidelines](#id-format-guidelines) below)
- `quote`: The actual quote text
- `speakers`: Everyone who speaks in the quote, comma-separated, in the order they
  speak. Use `""` if you don't know. Names must be spelled exactly as they appear in
  [Character Names](#character-names).

**Optional fields:**
- `context`: Episode information for reference
- `imageUrl`: Filename of associated image (if available on S3)

Plenty of quotes are exchanges rather than one-liners, which is why `speakers` is a
list rather than a single name:

```json
{
  "id": "quote-288",
  "quote": "Lucille: You tricked me. Michael: I deceived you, Mom. Trick makes it sound like we have a playful relationship. Lucille: Touche.",
  "speakers": "Lucille,Michael"
}
```

Note the format: comma-separated, **no space after the comma**, no duplicates even
when a character speaks twice.

### ID Format Guidelines

The existing data has inconsistent ID formats (`quote-001`, `quote-2`, `quote-3`, etc.). When adding new quotes:

1. **Find the highest existing ID number** by searching through quotes.json
2. **Use the next sequential number** with the format `quote-XXX` (e.g., if the highest is `quote-950`, use `quote-951`)
3. **Preferred format:** Use `quote-` prefix followed by the number (no specific padding required, though `quote-001` style is acceptable)

Example: If the last quote ID is `quote-500`, your new quote should be `quote-501`.

### Adding a New Quote

1. Open `app/data/quotes.json`
2. Find the highest existing quote ID number
3. Add your quote to the array with the next sequential ID
4. Ensure the JSON is valid (no trailing commas, proper syntax)
5. Include context information when possible

### Example Quote Addition

```json
{
  "id": "quote-042",
  "quote": "I don't understand the question, and I won't respond to it.",
  "speakers": "Lucille",
  "context": "Season 1, Episode 5 - Charity Drive"
}
```

### Verifying Your Quote Addition

After adding quotes:

```bash
# Start the server
uvicorn app.main:app --reload

# Test that quotes load correctly (note: may not show your new quote due to randomness)
curl http://localhost:8000/api/quotes/random

# Test character-specific quotes (if your quote names a speaker)
curl http://localhost:8000/api/quotes/lucille

# Check that every name you used is canonical
python scripts/normalize_speakers.py --check
```

**Note:** The `/random` endpoint returns a randomly selected quote, so you may need to call it multiple times to see your newly added quote. The character endpoint matches a quote if the requested name is *any* of its `speakers`, so `/api/quotes/michael` will return a quote whose speakers are `"Lucille,Michael"`.

## Character Names

`app/data/list-of-characters.txt` is the canonical list of character names. **Every
name in a `speakers` field must appear in that file, spelled exactly as it appears
there.**

This exists because the data used to drift. The same character showed up as `GOB`,
`Gob`, and `G.O.B.`; George Sr. showed up as `George`, `George Sr` and `George Sr.`.
The API filters quotes by exact name, so each spelling variant was effectively a
separate character, and `/api/quotes/gob` only ever returned a fraction of GOB's
quotes. One spelling per character fixes that.

Two conventions worth knowing:

- **Short names win when they're unambiguous.** It's `Michael`, `Tobias`, `Buster`,
  `Lindsay`, `Maeby`, `George Michael`, `Oscar` — not `Michael Bluth` or
  `Tobias Fünke`. Full names are only used where the short form collides with
  another character or isn't how the character is known: `Barry Zuckerkorn`,
  `Wayne Jarvis`, `Larry Middleman`.
- **`Lucille` is Lucille Bluth.** She's *the* Lucille. Lucille Austero is always
  written out as `Lucille Austero`.

### Checking your names

```bash
python scripts/normalize_speakers.py --check
```

This fails if a quote names a character that isn't on the list, or if the list has
drifted out of sync with the data. It's what CI runs on your PR, so run it before
you push.

An unrecognized name is a **hard stop in both modes** — `normalize_speakers.py`
writes nothing and exits non-zero until you either correct the quote or add the
character. It will not normalize around a name it doesn't know, because that
would delete a name you deliberately wrote and leave a record that looks fine
afterwards.

### Adding a character who isn't on the list yet

The list is **generated** — don't edit `list-of-characters.txt` by hand, your change
will be overwritten. Instead:

1. Add the character to the `CHARACTERS` dictionary in
   [`scripts/speaker_names.py`](scripts/speaker_names.py). The key is the canonical
   name; the value is a list of aliases that should resolve to it (nicknames, full
   names, spellings you've seen in the wild — the alias list is also what lets the
   parser recognize a `Name:` prefix in quote text).
2. Use the canonical name in your quote's `speakers` field.
3. Run `python scripts/normalize_speakers.py` to regenerate the list.
4. Commit both `quotes.json` and `list-of-characters.txt`.

If the character is a variant of someone already on the list, add an alias rather
than a new canonical name. `G.O.B.` belongs in GOB's alias list, not on the list as
its own entry.

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use type hints where appropriate
- Keep functions focused and single-purpose
- Write docstrings for public functions and classes

### Code Organization

- `app/main.py` - FastAPI routes and application setup
- `app/models.py` - Pydantic data models
- `app/services.py` - Business logic
- `app/config.py` - Configuration management
- `app/data/` - Static data files

### Documentation

- Update README.md if you add new features
- Add docstrings to new functions
- Update API documentation if endpoints change
- Include comments for complex logic

## Testing Guidelines

### Writing Tests

- Place tests in the `tests/` directory
- Name test files with `test_` prefix
- Use descriptive test function names
- Test both success and error cases

### Test Coverage

We aim for high test coverage. When adding new features:
- Write tests for happy paths
- Write tests for error conditions
- Test edge cases
- Verify HTTP status codes and response formats

### Example Test

```python
def test_random_quote_returns_valid_format(client):
    response = client.get("/api/quotes/random")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "quote" in data["data"]
    assert "speakers" in data["data"]
```

## Submitting Changes

### Before Submitting (quotes.json changes only)

- [ ] `quotes.json` is still valid JSON! Test with: `python3 -c "import json; json.load(open('app/data/quotes.json')); print('valid')"`
- [ ] Field values are consistent with other quotes (e.g., "Lucille" not "Lucille Bluth")
- [ ] Quotes are accurate (e.g., not "I've made a terrible mistake.")
- [ ] Commit messages are clear and descriptive

### Before Submitting (all else)

- [ ] Code follows the project style guidelines
- [ ] Tests pass locally (`pytest`)
- [ ] New features include tests
- [ ] Documentation is updated if needed
- [ ] Commit messages are clear and descriptive
- [ ] JSON files are valid (no syntax errors)

### Pull Request Process

1. **Push your changes to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Open a Pull Request** on GitHub with:
   - A clear title describing the change
   - A description of what changed and why
   - Reference to any related issues (e.g., "Fixes #123")
   - Screenshots for UI changes (if applicable)

3. **Respond to feedback**:
   - Address any review comments
   - Make requested changes
   - Push updates to your branch (PR will update automatically)

4. **Wait for approval**:
   - A maintainer will review your PR
   - Once approved, it will be merged

### Commit Message Guidelines

Write clear, concise commit messages:

```bash
# Good examples
git commit -m "Add quotes from Season 2 Episode 5"
git commit -m "Fix case-insensitive speaker matching bug"
git commit -m "Update README with Docker deployment instructions"

# Less helpful examples
git commit -m "fixes"
git commit -m "updates"
git commit -m "WIP"
```

## Questions?

If you have questions about contributing:
- Check the [README.md](README.md) for project documentation
- Review existing [issues](https://github.com/bbhart/bluthsapi/issues)
- Open a new issue with your question

For anything you would rather not put in a public issue, DM
[@bluthquotes.lucille2.com](https://bsky.app/profile/bluthquotes.lucille2.com) on Bluesky.

## License

By contributing to this project, you agree that your contributions will be licensed under the project's MIT License.

---

Thank you for contributing to the Arrested Development Quotes API! We appreciate your help in making this project better.
