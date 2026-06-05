# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pylustrator is an interactive Python tool for reproducible figure creation in scientific publications. It provides a GUI integrated with Matplotlib that allows users to interactively drag/resize plot elements, adjust formatting, and automatically generate Python code that reproduces all modifications.

## Build & Development Commands

```bash
# Install dependencies
uv sync

# Install with dev dependencies (includes ruff linter)
uv sync --extra dev

# Install with test dependencies
uv sync --extra test

# Run tests
uv run pytest

# Run tests in headless mode (required for CI/Linux)
QT_QPA_PLATFORM=offscreen uv run pytest

# Run a single test
uv run pytest tests/test_axes.py::TestAxes::test_method_name

# Lint with ruff
uv run ruff check .

# Build documentation
uv sync --group docs
uv run sphinx-build -b html docs docs/_build
```

## Architecture

### Core Flow
```
pylustrator.start() → patches plt.figure/plt.show
    ↓
PlotWindow (Qt GUI) created for each figure
    ↓
DragManager handles interactions → Selection manages multi-element transforms
    ↓
ChangeTracker monitors modifications → generates Python code
    ↓
Code inserted into source file before plt.show()
```

### Key Modules

| Module | Purpose |
|--------|---------|
| `QtGuiDrag.py` | Entry point; patches matplotlib, creates PlotWindow |
| `change_tracker.py` | Tracks modifications, generates reproducible Python code, manages undo/redo |
| `drag_helper.py` | Mouse interactions, object selection, grabber classes |
| `snap.py` | Alignment snapping; `TargetWrapper` provides unified interface for matplotlib objects |
| `QLinkableWidgets.py` | `Linkable` mixin binds Qt widgets to matplotlib artist properties bidirectionally |
| `components/plot_layout.py` | Graphics scene/view management, DPI awareness |
| `components/qitem_properties.py` | Property editor panel (largest component) |
| `helper_functions.py` | Utility functions like `fig_text()`, `add_axes()`, `changeFigureSize()` |

### Key Patterns

1. **Matplotlib Monkey-Patching**: `initialize()` patches `plt.figure()` and `plt.show()` to create GUI windows

2. **TargetWrapper**: Unified interface for all matplotlib artists in `snap.py`:
   ```python
   wrapper = TargetWrapper(matplotlib_artist)
   position = wrapper.get_position()
   wrapper.set_position([x, y, w, h])
   ```

3. **Linkable Mixin**: Qt widgets auto-sync with matplotlib properties in `QLinkableWidgets.py`

4. **Stack Introspection**: `ChangeTracker` uses traceback to find where to insert generated code in source files

5. **Special Attributes**: Objects use `_pylustrator_*` attributes for tracking:
   - `_pylustrator_reference` - object creation location
   - `_pylustrator_old_args` - initial property values
   - `_pylustrator_cached_*` - property caching

### Testing

Tests use `BaseTest` class from `tests/base_test_class.py` with helpers:
- `run_plot_script()` - creates and runs test figures
- `move_element()` - simulates drag operations
- `check_line_in_file()` - verifies generated code
- `change_property2()` - tests property modifications

## Dependencies & Compatibility

- Python 3.9+
- Matplotlib 2.0+ (branching for 3.6.0+ features)
- PyQt5 5.6+ (with PyQt6/PySide6 support)
- macOS Retina/DPI awareness is actively maintained

## Current Development Focus

The `fix_mac_display` branch addresses macOS display scaling with DPR (Device Pixel Ratio) awareness in `plot_layout.py`, `drag_helper.py`, and `snap.py`.
