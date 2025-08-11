# Template - AI Rooms Workflow Addon

## Overview

Addon for Rooms AI

**Addon Type:** `template` 

## Features

Here a quick summary of actions and what is possible.

## Add to Rooms AI using poetry

Using the script

```bash
poetry add git+https://github.com/synvex-ai/template-rooms-pkg.git
```

In the web interface, follow online guide for adding an addon. You can still use JSON in web interface.


## Configuration

### Addon Configuration
Add this addon to your AI Rooms workflow configuration:

```json
{
  "addons": [
    {
      "id": "my-addon-instance",
      "type": "addon-name",
      "name": "Descriptive Name",
      "enabled": true,
      "config": {
        "param1": "value1",
        "param2": 5432,
        "param3": "setting"
      },
      "secrets": {
        "credential1": "ENV_VAR_1",
        "credential2": "ENV_VAR_2"
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
| `type` | string | Yes | - | Type of the addon ("template") |
| `name` | string | Yes | - | Display name of the addon |
| `description` | string | Yes | - | Description of the addon |
| `enabled` | boolean | No | true | Whether the addon is enabled |

#### CustomAddonConfig Fields (template-specific)
This template addon adds these specific configuration fields:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `param1` | string | Yes | - | Example secret 1 |
| `param2` | string | Yes | - | Example secret 2 |
| `param3` | integer | No | 5432 | Example secret 3 |

### Required Secrets

| Secret Key | Environment Variable | Description |
|------------|---------------------|-------------|
| `credential1` | `ENV_VAR_1` | [Description] |
| `credential2` | `ENV_VAR_2` | [Description] |

### Environment Variables
Create a `.env` file in your workflow directory:

```bash
# .env file
ENV_VAR_1=your_value_here
ENV_VAR_2=your_secret_here
```

## Available Actions

### `example`
Demonstrates basic addon functionality with parameter processing and response generation.

**Parameters:**
- `param1` (string, required): First parameter for processing
- `param2` (string, required): Second parameter for processing

**Output Structure:**
- `result` (string): Processing result message
- `processed_data` (object): Contains the processed input parameters with timestamp

**Workflow Usage:**
```json
{
  "id": "example-processing",
  "action": "my-addon-instance::example",
  "parameters": {
    "param1": "{{payload.input_data}}",
    "param2": "configuration value"
  }
}
```

### `action-name-two`

Example of another addon action.

**Parameters:**
- `input_data` (string, required): Data to process
- `options` (object, optional): Processing options
  - `format` (string, default: "json"): Output format
  - `validate` (boolean, default: true): Enable validation

**Output Structure:**
- `status` (string): Operation status (success/error)
- `data` (object): Processed results
- `count` (integer): Number of items processed

**Workflow Usage:**
```json
{
  "id": "process-data",
  "action": "my-addon-instance::action-name-two",
  "parameters": {
    "input_data": "{{example-processing.output.processed_data}}",
    "options": {
      "format": "xml",
      "validate": false
    }
  }
}
```

## Tools Support (only for 'agent' type addons)

This agent addon support tools for .

The addon includes a tool registry that allows external tools to be registered and used within actions.

Agent addons can use different types of tools, for this, refer to 


## Testing & Lint

Like all Rooms AI deployments, addons should be roughly tested.

A basic PyTest is setup with a cicd to require 90% coverage in tests. Else it will not deploy the new release.

We also have ruff set up in cicd.

### Running the Tests

```bash
poetry run pytest tests/ --cov=src/template_rooms_pkg --cov-report=term-missing
```

### Running the linter

```bash
poetry run ruff check . --fix
```

### Pull Requests & versioning

Like for all deployments, we use semantic versioning in cicd to automatize the versions.

For this, use the apprioriate commit message syntax for semantic release in github.


## Developers / Mainteners

- Adrien EPPLING :  [Contact me](adrienesofts@gmail.com)
