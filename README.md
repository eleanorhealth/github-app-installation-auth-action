# Github App Installtion Auth Action

Authenticate as a github app installation and generate a token.

You will need to create a [GitHub App for authentication](https://docs.github.com/en/developers/apps/building-github-apps/authenticating-with-github-apps).

Once you have created an app, save the private key and app ID in secrets for the repo where you wish to run this action.

This action will return you your GitHub App's installation access token, which you can in turn use to invoke other GitHub APIs.

## Usage

### Input

| Key                     |   Type   | Required | Description                                                                |
| ----------------------- | :------: | :------: | -------------------------------------------------------------------------- |
| `app-id`                | `int`    |   Yes    | Your GitHub App's id                                                       |
| `private-key`           | `string` |   Yes    | The private key associated to the GitHub App (typically an RSA private key)|

**Be sure to store your `privateKey` [as a secret](https://docs.github.com/en/actions/configuring-and-managing-workflows/creating-and-storing-encrypted-secrets) in GitHub Actions!**

### Output

This action returns the relevant installation token for use in subsequent steps, like [actions/github-script](https://github.com/actions/github-script)

| Property              | Type      | Description                                                                                                                            |
| --------------------- | --------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `github_app_token`    | `string`  | A GitHub App [installation access token](https://docs.github.com/en/rest/reference/apps#create-an-installation-access-token-for-an-app)|

### GitHub Workflow

```yaml
---
name: demo
on:
  pull_request:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Authenticate as Github App Installation
        id: auth-github
        uses: eleanorhealth/github-app-installation-auth-action
        with:
          private-key: ${{ secrets.PRIVATE_KEY }}
          app-id: ${{ secrets.DEPLOYER_GITHUB_APP_ID}}
      - name: Configure git
        id: configure-git
        shell: bash
        run: |
          git config --global url."https://x-access-token:${{ steps.auth-github.outputs.github_app_token }}@github.com/yourorg".insteadOf "https://github.com/yourorg"
```

## Dependency management

This project uses [pip-tools](https://pypi.org/project/pip-tools/) for hard-pinning dependencies versions.
Please see its documentation for usage instructions.
In short, `requirements.in` contains the list of direct requirements with occasional version constraints and `requirements.txt` is automatically generated from it by adding recursive tree of dependencies with fixed versions.

To upgrade dependency versions, run `pip-compile --generate-hashes` at the root of the repo.

To add a new dependency without upgrade, add it to `requirements.in` and run `pip-compile  --generate-hashes --no-upgrade`.

For installation always use `.txt` files. For example, command `pip install -Ue . -r requirements.txt` will install this project in development mode, testing requirements and development tools.
Another useful command is `pip-sync requirements.txt`, it uninstalls packages from your virtualenv that aren't listed in the file.
