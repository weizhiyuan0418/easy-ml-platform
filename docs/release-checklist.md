# Release Checklist

Use this checklist before publishing a new public release.

## Source Validation

- [ ] Run `.\.venv\Scripts\python.exe manage.py test`
- [ ] Run `.\.venv\Scripts\python.exe tools\verify_project.py`
- [ ] Run `.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run`
- [ ] Run `node --check static\mlapp\app.js`
- [ ] Run `.\.venv\Scripts\python.exe tools\cleanup_model_artifacts.py`

## Manual Smoke Test

- [ ] Start from a fresh local data directory.
- [ ] Load the sample project.
- [ ] Train all outputs and confirm an active model appears.
- [ ] Run a prediction.
- [ ] Check Chinese and English language switching.
- [ ] Check the Data page pagination when records exceed one page.
- [ ] Confirm common errors are readable: no file import, unknown columns, no active model, missing model file.

## Packaging

- [ ] Run `.\packaging\build_windows_installer.ps1`
- [ ] Install the generated Windows installer locally.
- [ ] Confirm the desktop shell runs migrations and opens the local Web UI.
- [ ] Generate SHA256 for the installer.
- [ ] Update `README.md` installer links and SHA256 values.

## GitHub

- [ ] Commit the release changes.
- [ ] Push to `main`.
- [ ] Wait for GitHub Actions to pass on Python 3.12, 3.13, and 3.14.
- [ ] Create the GitHub Release with the installer and `.sha256.txt` asset.
- [ ] Reopen the README links and confirm assets download.
