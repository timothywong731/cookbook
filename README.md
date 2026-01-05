# Quickstart Template

A clean and modern Python project template using Poetry for dependency management, Pytest for testing, and Pre-commit for code quality.

## Features

- **Dependency Management**: Managed by [Poetry](https://python-poetry.org/).
- **Code Quality**: Integrated with [Black](https://github.com/psf/black), [isort](https://github.com/PyCQA/isort), and [Flake8](https://flake8.pycqa.org/).
- **Testing**: Robust testing setup with [Pytest](https://docs.pytest.org/) and coverage reporting.
- **Pre-commit Hooks**: Automatically runs linters and formatters on every commit.
- **Notebook Support**: Includes Jupyter kernel setup and `nbstripout` for clean notebook version control.

## Prerequisites

- Python 3.13 or higher.
- [Poetry](https://python-poetry.org/docs/#installation) installed on your system.

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd quickstart
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Set up pre-commit hooks:
   ```bash
   poetry run pre-commit install
   ```

## Usage

### Running the Application

You can run the main entry point using the Poetry script:

```bash
poetry run app
```

Or directly via Python:

```bash
poetry run python quickstart/main.py
```

### Running Tests

Run the test suite with Pytest:

```bash
poetry run pytest
```

To generate a coverage report:

```bash
poetry run pytest --cov=quickstart
```

The HTML coverage report will be available in the `htmlcov/` directory.

## Development

### Linting and Formatting

The project uses `black`, `isort`, and `flake8`. You can run them manually:

```bash
# Format code
poetry run black .
poetry run isort .

# Lint code
poetry run flake8 .
```

### Pre-commit

Pre-commit hooks are configured to run automatically on `git commit`. You can also run them manually on all files:

```bash
poetry run pre-commit run --all-files
```

## Project Structure

```text
quickstart/
├── notebooks/          # Jupyter notebooks for exploration
├── quickstart/         # Main package source code
│   ├── utils/          # Utility modules
│   └── main.py         # Application entry point
├── tests/              # Unit tests
├── pyproject.toml      # Project configuration and dependencies
└── README.md           # Project documentation
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

 pyproject.toml      # Project configuration and dependencies
 README.md           # Project documentation
`

## License

This project is licensed under the MIT License - see the LICENSE file for details.
