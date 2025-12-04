# OpenAI - AI Rooms Workflow Addon

## Overview

OpenAI GPT-powered AI agent addon for Rooms AI, providing advanced text generation and conversational AI capabilities.

**Addon Type:** `openai` ( 'agent' type addon )

## Features

- **Text Generation**: Advanced text generation using OpenAI GPT models
- **Chat Completion**: Conversational AI with GPT-3.5 and GPT-4 models
- **Flexible Configuration**: Customizable model, temperature, and token limits
- **Token Tracking**: Comprehensive token usage monitoring
- **Tool Registry**: Support for external tools and workflow integration

## Add to Rooms AI using poetry

Using the script

```bash
poetry add git+https://github.com/synvex-ai/openai-rooms-pkg.git
```

In the web interface, follow online guide for adding an addon. You can still use JSON in web interface.


## Configuration

### Addon Configuration
Add this addon to your AI Rooms workflow configuration:

```json
{
  "addons": [
    {
      "id": "gpt-assistant",
      "type": "openai",
      "name": "OpenAI GPT Assistant",
      "enabled": true,
      "config": {
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "max_tokens": 1000
      },
      "secrets": {
        "openai_api_key": "OPENAI_API_KEY"
      }
    }
  ]
}
```

### Configuration Fields

#### BaseAddonConfig Fields
All addons inherit these base configuration fields:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | string | Yes | - | Unique identifier for the addon instance |
| `type` | string | Yes | - | Type of the addon ("openai") |
| `name` | string | Yes | - | Display name of the addon |
| `description` | string | Yes | - | Description of the addon |
| `enabled` | boolean | No | true | Whether the addon is enabled |

#### CustomAddonConfig Fields (openai-specific)
This OpenAI addon adds these specific configuration fields:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `model` | string | No | "gpt-3.5-turbo" | OpenAI model to use (gpt-3.5-turbo, gpt-4, gpt-4-turbo, etc.) |
| `temperature` | float | No | 0.7 | Temperature for text generation (0.0-2.0) |
| `max_tokens` | integer | No | 1000 | Maximum tokens for responses |

### Required Secrets

| Secret Key | Environment Variable | Description |
|------------|---------------------|-------------|
| `openai_api_key` | `OPENAI_API_KEY` | OpenAI API key for accessing GPT models |

### Environment Variables
Create a `.env` file in your workflow directory:

```bash
# .env file
OPENAI_API_KEY=your_openai_api_key_here
```

## Available Actions

### `generate_text`
Generate text using OpenAI GPT models with customizable parameters.

**Parameters:**
- `prompt` (string, required): Text prompt for the model to generate a response

**Output Structure:**
- `generated_text` (string): The generated text response
- `model_used` (string): Model that was used for generation
- `usage` (object): Token usage information
  - `prompt_tokens` (integer): Number of tokens in the prompt
  - `completion_tokens` (integer): Number of tokens in the completion
  - `total_tokens` (integer): Total tokens used
- `timestamp` (string): ISO format timestamp of the generation

**Workflow Usage:**
```json
{
  "id": "generate-content",
  "name": "Generate Content",
  "action": "gpt-assistant::generate_text",
  "parameters": {
    "prompt": "{{payload.user_question}}"
  }
}
```

**Example with Dynamic Prompt:**
```json
{
  "id": "summarize-document",
  "name": "Summarize Document",
  "action": "gpt-assistant::generate_text",
  "parameters": {
    "prompt": "Summarize the following document: {{payload.document_content}}"
  }
}
```

**Example with Context:**
```json
{
  "id": "answer-question",
  "name": "Answer Question",
  "action": "gpt-assistant::generate_text",
  "parameters": {
    "prompt": "Based on this context: {{previous-step.output.context}}\n\nAnswer this question: {{payload.question}}"
  }
}
```

## Tools Support

This agent addon **supports tools** for enhanced functionality.

### Tool Integration
The addon includes a tool registry that allows external tools to be registered and used within actions. Tools can be integrated via `useStorage` or `useContext` in workflow configurations.

**Note:** Tool support in OpenAI addon follows the standard Rooms AI tool integration pattern, allowing the model to interact with external services and databases.

### Using Tools with OpenAI
When tools are registered via `useStorage` or `useContext`, they become available during action execution:

```json
{
  "id": "gpt-with-database",
  "name": "GPT with Database Access",
  "action": "gpt-assistant::generate_text",
  "useStorage": {
    "addonId": "my-mongo-db",
    "action": [
      {"name": "describe", "description": "Get database information"},
      {"name": "insert", "description": "Insert data into database"}
    ]
  },
  "parameters": {
    "prompt": "Analyze our database and provide insights about user activity"
  }
}
```

For detailed tool usage patterns, refer to the [AI Features documentation](../ai-features).


## Usage Examples

### Basic Text Generation
```json
{
  "addons": [
    {
      "id": "gpt-assistant",
      "type": "openai",
      "name": "OpenAI GPT Assistant",
      "enabled": true,
      "config": {
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "max_tokens": 1000
      },
      "secrets": {
        "openai_api_key": "OPENAI_API_KEY"
      }
    }
  ],
  "entrypoints": [
    {
      "id": "default",
      "name": "Text Generation Workflow",
      "startAt": "generate-response"
    }
  ],
  "workflow": {
    "id": "text-generation",
    "name": "Text Generation Workflow",
    "version": "1.0.0",
    "steps": [
      {
        "id": "generate-response",
        "name": "Generate Response",
        "action": "gpt-assistant::generate_text",
        "parameters": {
          "prompt": "{{payload.user_input}}"
        }
      }
    ]
  }
}
```

### Advanced Configuration with GPT-4
```json
{
  "addons": [
    {
      "id": "gpt4-assistant",
      "type": "openai",
      "name": "GPT-4 Assistant",
      "enabled": true,
      "config": {
        "model": "gpt-4-turbo",
        "temperature": 0.5,
        "max_tokens": 2000
      },
      "secrets": {
        "openai_api_key": "OPENAI_API_KEY"
      }
    }
  ]
}
```

### Multi-Step Workflow with Context
```json
{
  "workflow": {
    "id": "analysis-workflow",
    "name": "Analysis Workflow",
    "version": "1.0.0",
    "steps": [
      {
        "id": "extract-key-points",
        "name": "Extract Key Points",
        "action": "gpt-assistant::generate_text",
        "parameters": {
          "prompt": "Extract key points from: {{payload.document}}"
        },
        "next": ["generate-summary"]
      },
      {
        "id": "generate-summary",
        "name": "Generate Summary",
        "action": "gpt-assistant::generate_text",
        "parameters": {
          "prompt": "Create a summary based on these key points: {{extract-key-points.output.generated_text}}"
        }
      }
    ]
  }
}
```


## Testing & Lint

Like all Rooms AI deployments, addons should be roughly tested.

A basic PyTest is setup with a cicd to require 90% coverage in tests. Else it will not deploy the new release.

We also have ruff set up in cicd.

### Running the Tests

```bash
poetry run pytest tests/ --cov=src/openai_rooms_pkg --cov-report=term-missing
```

### Running the linter

```bash
poetry run ruff check . --fix
```

### Pull Requests & versioning

Like for all deployments, we use semantic versioning in cicd to automatize the versions.

For this, use the apprioriate commit message syntax for semantic release in github.


## Developers / Mainteners

- Adrien EPPLING :  [adrien.eppling@nexroo.ai](mailto:adrien.eppling@nexroo.ai)
