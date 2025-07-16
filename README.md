# Template Rooms Package

A template Python package for the AI rooms script addon system.

## Overview

This package provides a basic template implementation for creating addon packages that can be loaded by the AI rooms script. It includes an addon class with a `test()` method that validates the package functionality.

## Installation

```bash
pip install -e .
```

## Usage

This package is designed to be imported by the AI rooms script's `loadAddons` functionality. The package provides an addon class that can be instantiated and used:

```python
from template_rooms_pkg.addon import TemplateRoomsAddon

# Instantiate the addon
addon = TemplateRoomsAddon()

# Test the addon functionality
result = addon.test()
```

The AI rooms script automatically discovers and instantiates the addon class from the `addon.py` module, so manual instantiation is typically not required in production use.

## Creating a New Addon from Template

To create a new addon package using this template:

1. **Clone or fork this repository**
2. **Rename the package directory and references:**
   - Rename `src/template_rooms_pkg/` to `src/{your_addon_name}_rooms_pkg/`
   - Update `pyproject.toml`:
     - Change package name from `template-rooms-pkg` to `{your-addon-name}-rooms-pkg`
     - Update module path in `[tool.setuptools.packages.find]`
   - Update imports in `src/{your_addon_name}_rooms_pkg/addon.py`
3. **Update the addon class:**
   - Rename `TemplateRoomsAddon` to `{YourAddonName}RoomsAddon` in `addon.py`
   - Customize the `test()` method and add your addon functionality
4. **Update documentation:**
   - Modify this README.md with your addon's specific information
   - Update the CHANGELOG.md

### Required File Structure

```
src/
└── {your_addon_name}_rooms_pkg/
    ├── __init__.py
    ├── addon.py              # Contains your addon class
    ├── actions/
    ├── configuration/
    ├── memory/
    ├── services/
    ├── storage/
    ├── tools/
    └── utils/
```

## CI/CD

The project uses semantic release for automated versioning and publishing:

- **Automated Versioning**: Semantic release analyzes commit messages to determine version bumps
- **Automated Publishing**: Releases are triggered automatically on pushes to the main branch
- **Commit Message Format**: Follow conventional commits format:
  - `feat:` for new features (minor version)
  - `fix:` for bug fixes (patch version)
  - `BREAKING CHANGE:` for breaking changes (major version)

### Release Process

1. Push changes to main branch
2. Semantic release automatically:
   - Analyzes commit history
   - Determines next version number
   - Generates changelog
   - Creates GitHub release
   - Publishes to PyPI (if configured)

## Development

The project uses semantic release for automated versioning. Releases are triggered automatically on pushes to the main branch.

## License

MIT
