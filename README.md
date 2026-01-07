# Cookbook Recipe Generator

Create a cookbook by extracting structured recipes from your Google Photos album and generating watercolor-style illustrations with Azure OpenAI.

## Features

- **Google Photos ingestion**: Pulls recipe images from a named album.
- **Image preprocessing**: Normalizes to a target aspect ratio and splits when needed.
- **Azure OpenAI extraction**: Extracts structured recipe data with Pydantic validation.
- **Watercolor illustrations**: Generates a consistent style illustration from reference images.
- **Markdown output**: Produces a recipe markdown file that includes the illustration.

## Prerequisites

- Python 3.13 or higher.
- [Poetry](https://python-poetry.org/docs/#installation) installed on your system.

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd vibe_cookbook
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

## Usage

### Required Environment Variables

```bash
export GOOGLE_CLIENT_SECRET=/path/to/google-client-secret.json
export GOOGLE_TOKEN=/path/to/google-token.json
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
export AZURE_OPENAI_API_KEY=your-api-key
export AZURE_OPENAI_API_VERSION=2024-02-01
export AZURE_OPENAI_CHAT_DEPLOYMENT=your-chat-deployment
export AZURE_OPENAI_IMAGE_DEPLOYMENT=your-image-deployment
```

### Running the Application

You can run the main entry point using the Poetry script:

```bash
poetry run app \
  --album-name recipe \
  --output-dir output \
  --aspect-ratio 0.8 \
  --split-margin-ratio 0.08 \
  --reference-style-dir reference_style
```

Or directly via Python:

```bash
poetry run python cookbook/main.py
```

## Running Tests

Run the test suite with Pytest:

```bash
poetry run pytest
```

## Project Structure

```text
vibe_cookbook/
├── notebooks/          # Jupyter notebooks for exploration
├── cookbook/           # Main package source code
│   ├── utils/          # Utility modules
│   └── main.py         # Application entry point
├── tests/              # Unit tests
├── pyproject.toml      # Project configuration and dependencies
└── README.md           # Project documentation
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
