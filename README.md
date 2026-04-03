# GitHub App Installation Auth Action

Authenticate as a GitHub App installation and generate a short-lived access token.

This action implements the [GitHub App authentication flow](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation) — it mints a JWT from your App's private key, exchanges it for an installation access token via the GitHub API, and exposes that token as a step output for use in subsequent workflow steps.

## How It Works

1. A short-lived JWT (10-minute expiry) is signed using the App's RSA private key.
2. The JWT is used to call `GET /app/installations` and retrieve the first installation ID.
3. The installation ID is used to call `POST /app/installations/{id}/access_tokens`, returning a scoped access token (valid for ~1 hour).

The token is printed to stdout, captured, and written to `$GITHUB_OUTPUT`.

## Prerequisites

You need a GitHub App with:
- An RSA private key (download from the App settings page)
- The App installed on the organization or repository where the workflow runs

Store the private key and App ID as [encrypted secrets](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions) in your repository or organization.

## Usage

### Inputs

| Input         | Type     | Required | Description                                      |
| ------------- | :------: | :------: | ------------------------------------------------ |
| `app-id`      | `string` | Yes      | Your GitHub App's numeric ID                     |
| `private-key` | `string` | Yes      | The RSA private key associated with the App (PEM format) |

### Outputs

| Output              | Type     | Description                                                                                                                         |
| ------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `github_app_token`  | `string` | A GitHub App [installation access token](https://docs.github.com/en/rest/apps/apps#create-an-installation-access-token-for-an-app) |

### Example Workflow

```yaml
---
name: Example
on:
  pull_request:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Authenticate as GitHub App Installation
        id: auth-github
        uses: eleanorhealth/github-app-installation-auth-action@main
        with:
          private-key: ${{ secrets.GITHUB_APP_PRIVATE_KEY }}
          app-id: ${{ secrets.GITHUB_APP_ID }}

      - name: Use the token
        run: |
          echo "Token acquired, length: ${#TOKEN}"
        env:
          TOKEN: ${{ steps.auth-github.outputs.github_app_token }}
```

### Common Use Case: Git Authentication

A common pattern is to configure git to use the token for HTTPS cloning of private repositories:

```yaml
      - name: Configure git with App token
        run: |
          git config --global url."https://x-access-token:${TOKEN}@github.com/your-org".insteadOf \
            "https://github.com/your-org"
        env:
          TOKEN: ${{ steps.auth-github.outputs.github_app_token }}
```

> **Security note:** The token is valid for approximately 1 hour. It is automatically revoked when it expires. Never log or expose the token value in workflow output.

## Implementation Details

The action is a [composite action](https://docs.github.com/en/actions/creating-actions/creating-a-composite-action) that:

1. Installs Python 3.11 via `actions/setup-python@v5`
2. Installs pinned Python dependencies from `requirements.txt`
3. Runs `src/github_app_token.py` with `--direct` mode, passing the App ID and private key as arguments

The Python script supports four input modes (all mutually exclusive):

| Flag        | Description                                              |
| ----------- | -------------------------------------------------------- |
| `--direct`  | Pass `--app-id` and `--private-key` as CLI arguments     |
| `--env`     | Read a JSON blob from the named environment variable     |
| `--file`    | Read a JSON blob from the given file path                |
| `--inline`  | Pass a JSON blob directly on the command line            |

When using `--env`, `--file`, or `--inline`, the JSON must contain `DEPLOYER_GITHUB_APP_ID` and `PRIVATE_KEY` keys.

## Dependencies

| Package       | Purpose                                      |
| ------------- | -------------------------------------------- |
| `PyJWT`       | Signs the JWT bearer token (RS256)           |
| `cryptography`| RSA key loading for PyJWT                    |
| `requests`    | HTTP calls to the GitHub API                 |
| `certifi`     | Up-to-date CA bundle for TLS verification    |

Dependencies are managed with [pip-tools](https://pip-tools.readthedocs.io/). All packages are pinned to exact versions with SHA-256 hashes in `requirements.txt` for reproducible, tamper-evident installs.

### Updating Dependencies

```bash
# Upgrade all dependencies to their latest compatible versions
pip-compile --generate-hashes --upgrade

# Add a new dependency without upgrading existing ones
# 1. Add it to requirements.in
# 2. Run:
pip-compile --generate-hashes --no-upgrade

# Sync your local environment exactly to requirements.txt
pip-sync requirements.txt
```
