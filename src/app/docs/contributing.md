# Contributing Guide

Thank you for your interest in contributing to the EmbedIQ backend! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

Please read and follow our [Code of Conduct](code_of_conduct.md) to foster an inclusive and respectful community.

## Getting Started

### Prerequisites

- Python 3.10 or later
- PostgreSQL 14 or later
- Git

### Setting Up the Development Environment

1. Fork the repository on GitHub.

2. Clone your fork locally:

```bash
git clone https://github.com/yourusername/embediq-backend.git
cd embediq-backend
```

3. Set up a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

5. Set up the database:

Follow the instructions in the [Database Setup](database_setup.md) documentation.

6. Configure environment variables:

Create a `.env` file in the project root with the following variables:

```bash
DATABASE_URL=postgresql://username:password@localhost:5432/embediq
AUTH0_DOMAIN=your-auth0-domain.auth0.com
AUTH0_API_AUDIENCE=your-auth0-api-audience
AUTH_DISABLED=true  # For development
DATA_DIR=./data/embediq/users
```

7. Run the development server:

```bash
cd src
python run_dev_server.py --reload
```

## Development Workflow

### Branching Strategy

We use a simplified Git flow with the following branches:

- `main`: The main branch contains the latest stable release.
- `develop`: The development branch contains the latest development changes.
- Feature branches: Create a new branch for each feature or bug fix.

### Creating a Feature Branch

```bash
# Make sure you're on the develop branch
git checkout develop
git pull origin develop

# Create a new feature branch
git checkout -b feature/your-feature-name
```

### Making Changes

1. Make your changes to the codebase.
2. Write tests for your changes.
3. Run the tests to ensure they pass:

```bash
pytest
```

4. Format your code using Black:

```bash
black src/
```

5. Lint your code using Flake8:

```bash
flake8 src/
```

### Committing Changes

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification for commit messages:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `style`: Changes that do not affect the meaning of the code (formatting, etc.)
- `refactor`: Code changes that neither fix a bug nor add a feature
- `perf`: Performance improvements
- `test`: Adding or fixing tests
- `chore`: Changes to the build process or auxiliary tools

Example:

```
feat(documents): add support for PDF documents

- Add PDF parsing using PyPDF2
- Add unit tests for PDF parsing
- Update documentation

Closes #123
```

### Submitting a Pull Request

1. Push your feature branch to your fork:

```bash
git push origin feature/your-feature-name
```

2. Create a pull request from your fork to the `develop` branch of the main repository.

3. Fill out the pull request template with details about your changes.

4. Wait for the CI/CD pipeline to run and ensure all tests pass.

5. Address any feedback from the code review.

6. Once approved, your pull request will be merged into the `develop` branch.

## Code Style

We follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide for Python code with some modifications:

- Line length: 88 characters (Black default)
- Use double quotes for strings
- Use trailing commas in multi-line collections

We use the following tools to enforce code style:

- [Black](https://black.readthedocs.io/): Code formatter
- [Flake8](https://flake8.pycqa.org/): Linter
- [isort](https://pycqa.github.io/isort/): Import sorter

### Pre-commit Hooks

We recommend using pre-commit hooks to automatically check your code before committing:

```bash
pip install pre-commit
pre-commit install
```

## Testing

We use pytest for testing. See the [Testing](testing.md) documentation for more details.

### Writing Tests

- Write unit tests for all new code.
- Write integration tests for API endpoints.
- Aim for high test coverage.

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=app

# Run specific tests
pytest src/tests/unit/test_file.py
```

## Documentation

We use Markdown for documentation. All documentation files are stored in the `src/app/docs` directory.

### Writing Documentation

- Use clear and concise language.
- Include code examples where appropriate.
- Follow the existing documentation structure.
- Update documentation when making changes to the codebase.

### Building Documentation

The documentation is served directly from the Markdown files using the documentation API endpoints.

## API Design

We follow RESTful API design principles:

- Use resource-based URLs.
- Use HTTP methods appropriately (GET, POST, PUT, PATCH, DELETE).
- Use HTTP status codes correctly.
- Use consistent response formats.
- Use query parameters for filtering, sorting, and pagination.
- Use request and response validation.

### API Versioning

We use URL-based versioning for the API:

```
/api/v1/resource
```

### API Documentation

We use FastAPI's automatic documentation generation for API documentation. The documentation is available at:

- Swagger UI: `/docs`
- ReDoc: `/redoc`

## Database Schema

See the [Database Setup](database_setup.md) documentation for information on the database schema.

## Reporting Issues

If you find a bug or have a feature request, please create an issue on GitHub:

1. Go to the [Issues](https://github.com/yourusername/embediq-backend/issues) page.
2. Click the "New Issue" button.
3. Select the appropriate issue template.
4. Fill out the template with details about the bug or feature request.

## Security Vulnerabilities

If you discover a security vulnerability, please do NOT open an issue. Email security@embediq.com instead.

## License

By contributing to this project, you agree that your contributions will be licensed under the project's license.
