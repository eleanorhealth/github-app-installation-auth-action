# Github App Installtion Auth Action

Authenticate as a github app installation

## Usage

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
      - configure-git:
        shell: bash
        run: |
          git config --global url."https://x-access-token:${{ steps.auth-github.outputs.github_app_token }}@github.com/eleanorhealth".insteadOf "https://github.com/eleanorhealth"
```
