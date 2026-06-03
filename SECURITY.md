# Security Policy

## Supported versions

The current `main` branch is the supported development version.

## Reporting a vulnerability

Please do not publish vulnerabilities, credentials, tokens, or private datasets in public issues.

Report security concerns by opening a private GitHub security advisory if available, or by contacting the repository owner directly through GitHub.

## Sensitive files

Do not commit:

- `.env` or other local environment files
- `db.sqlite3`
- trained model artifacts
- API tokens, passwords, private keys, certificates, or account credentials
- private datasets

The repository `.gitignore` is configured to exclude common local runtime files, but contributors are still responsible for checking `git status` before committing.
