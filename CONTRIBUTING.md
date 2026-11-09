# Contributing to Clacktivity

Thanks for your interest in contributing. This document covers how to set up your development environment, run the app locally, and submit changes.

## Development setup

1. Fork the repository on GitHub and clone your fork locally:

```powershell
git clone https://github.com/<your-username>/Clacktivity.git
cd Clacktivity
```

2. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install the dependencies:

```powershell
pip install -r requirements.txt
```

## Running in development mode

By default, `python run.py` detaches into a background process. When developing or debugging, keep the process attached to your terminal so you can see logs and stop it with `Ctrl+C`:

```powershell
python run.py --foreground
```

If you are only working on the web dashboard or API and do not need the Windows keyboard hook or System Tray icon active, use:

```powershell
python run.py --foreground --no-tray --no-hook
```

## Running tests

Run the test suite before submitting a pull request to make sure everything passes:

```powershell
pytest -v
```

If you add a new feature or fix a bug, please include tests in the `tests/` directory.

## Project conventions

- Write all code, comments, docstrings, and commit messages in English.
- Keep modules focused and concise. Backend logic lives in `src/` and frontend modules live in `static/js/`.
- Do not commit local databases (`*.db`), log files (`*.log`), or `.env` files.
- Keep the frontend dependency-free (vanilla HTML, CSS, and ES modules) unless discussed in an issue first.

## Submitting a pull request

1. Create a new branch for your fix or feature:

```powershell
git checkout -b feat/your-feature-name
```

2. Make your changes and verify that `pytest -v` passes.
3. Commit your changes with a clear description of what changed and why.
4. Push the branch to your fork and open a Pull Request against `main`.

## Reporting bugs and suggesting features

When opening an issue on GitHub, please include:
- Your Windows version and Python version (`python --version`).
- Steps to reproduce the issue (if reporting a bug).
- Any relevant error output from the terminal or `data/app.log`.
