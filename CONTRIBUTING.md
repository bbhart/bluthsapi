# Contributing to Arrested Development Quotes API

Thank you for your interest in contributing to the Arrested Development Quotes API! We appreciate contributions of all kinds, from bug fixes and documentation improvements to new features and quote additions.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Contributing Quotes](#contributing-quotes)
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
- Docker (optional, for testing containerized deployment)

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

   # Install production dependencies
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
pytest tests/test_api.py -v
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

The quotes database lives in `app/data/quotes.json`. We welcome additions and corrections!

### Quote Format

Each quote should follow this structure:

```json
{
  "id": "quote-XXX",
  "quote": "The actual quote text here.",
  "primarySpeaker": "Character Name",
  "speakers": ["Character Name", "Other Character"],
  "context": "Season X, Episode Y - Episode Title",
  "imageUrl": "filename.jpg"
}
```

**Required fields:**
- `id`: Unique identifier (e.g., "quote-001", "quote-002")
- `quote`: The actual quote text
- `primarySpeaker`: The main character speaking

**Optional fields:**
- `speakers`: Array of all characters involved (if multiple)
- `context`: Episode information for reference
- `imageUrl`: Filename of associated image (if available on S3)

### Adding a New Quote

1. Open `app/data/quotes.json`
2. Add your quote to the `quotes` array
3. Ensure the JSON is valid (no trailing commas, proper syntax)
4. Use the next available quote ID number
5. Include context information when possible

### Example Quote Addition

```json
{
  "id": "quote-042",
  "quote": "I don't understand the question, and I won't respond to it.",
  "primarySpeaker": "Lucille",
  "speakers": ["Lucille"],
  "context": "Season 1, Episode 5 - Charity Drive"
}
```

### Verifying Your Quote Addition

After adding quotes:

```bash
# Start the server
uvicorn app.main:app --reload

# Test that quotes load correctly
curl http://localhost:8000/api/quotes/random

# Test character-specific quotes
curl http://localhost:8000/api/quotes/lucille
```

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
    assert "primarySpeaker" in data["data"]
```

## Submitting Changes

### Before Submitting

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

## License

By contributing to this project, you agree that your contributions will be licensed under the project's MIT License.

---

Thank you for contributing to the Arrested Development Quotes API! We appreciate your help in making this project better.
