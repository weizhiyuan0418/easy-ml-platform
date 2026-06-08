# Changelog

All notable changes are recorded here. This project follows a simple version history rather than a strict release specification.

## v0.2.2 - Usability and Maintenance Fixes

- Added paginated record loading in the Web UI to keep larger local datasets easier to browse.
- Added a dashboard data-quality summary for missing fields, numeric ranges, and category counts.
- Preserved existing active models when a later training attempt fails, and cleaned up replaced model artifacts after successful retraining.
- Added stable error codes for invalid project IDs, import file problems, missing model files, and model activation mistakes.
- Added a model artifact cleanup dry-run tool for maintenance.

## v0.2.1 - Stability and Public Repository Polish

- Added roadmap and changelog documentation.
- Expanded README FAQ for installer warnings, data storage, Python version, and suitable dataset size.
- Updated release version metadata for the `v0.2.1` installer.
- Kept the project scope focused on small local tabular machine learning experiments.

## v0.2.0 - Open Source Usability

- Added project selection, project creation, and one-click sample project loading.
- Improved quick-start guidance, bilingual UI messages, import preview, training feedback, and prediction display.
- Added real README screenshots and a Windows installer Release.
- Fixed misleading success feedback when training data is insufficient.
- Added CSV template download and structured user-facing API error codes.

## v0.1.1 - Rename and Bilingual README

- Renamed the product display name to Easy ML Platform.
- Added bilingual README content.

## v0.1.0 - Initial Public Package

- Added the initial Django-based local Web app for configurable tabular machine learning.
- Added one-click startup scripts and local Windows packaging support.
