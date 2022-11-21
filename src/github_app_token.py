#!/usr/bin/env python3

# pylint: disable=line-too-long
# Implementation of: https://docs.github.com/en/developers/apps/authenticating-with-github-apps#authenticating-as-a-github-app
# Inspired by https://gist.github.com/pelson/47c0c89a3522ed8da5cc305afc2562b0

# TL;DR
# Only GitHub App has an access to annotations API. In order to access this API, we need
# to generate a token based on GitHub App's private key and ID. The token (aka JWT) is
# valid for only 10 min.
# pylint: enable=line-too-long

"""Module for authenticating as a Github App Installation"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

# pyjwt
import jwt
import requests


def main():

    """Returns an Installation Access Token"""
    parser = argparse.ArgumentParser()
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "-e", "--env", help="Name of environment variable with JSON secrets.", type=str
    )
    source_group.add_argument(
        "-f", "--file", type=str, help="Path to file with JSON secrets."
    )
    source_group.add_argument("-i", "--inline", type=str, help="Inline JSON secrets.")
    source_group.add_argument(
        "-d",
        "--direct",
        help="Direct secrets.",
        default=False,
        action="store_true",
    )

    direct_group = parser.add_argument_group()
    direct_group.add_argument(
        "-p", "--private-key", type=str, help="GitHub App private key."
    )
    direct_group.add_argument("-a", "--app-id", type=str, help="GitHub App ID.")

    args = parser.parse_args()

    if args.env:
        try:
            secret_json = json.loads(os.getenv(args.env))
        except TypeError as exc:
            raise TypeError(f"{args.env} is not set") from exc
    elif args.file:
        try:
            with Path(args.file).open(encoding="UTF-8") as file:
                secret_json = json.load(file)
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"File {args.file} not found") from exc
    elif args.inline:
        try:
            secret_json = json.loads(args.inline)
        except ValueError as exc:
            raise ValueError("Invalid JSON") from exc

    if args.direct:
        if not args.private_key or not args.app_id:
            raise ValueError("--direct option requires --private-key and --app-id")
        private_key = args.private_key
        github_app_id = args.app_id
    else:
        try:
            github_app_id = secret_json["DEPLOYER_GITHUB_APP_ID"]
            private_key = secret_json["PRIVATE_KEY"]
        except KeyError as exc:
            raise KeyError(
                f"Secrets JSON is missing {exc} key. Make sure you have set "
                "DEPLOYER_GITHUB_APP_ID and PRIVATE_KEY."
            ) from exc

    if not private_key:
        raise ValueError("PRIVATE_KEY is empty")
    if not github_app_id:
        raise ValueError("DEPLOYER_GITHUB_APP_ID is empty")

    bearer = create_jwt(github_app_id, private_key)
    installation_id = get_installation_id(bearer)
    access_token = get_installation_access_token(installation_id, bearer)
    print(access_token)


def create_jwt(github_app_id: str, private_key: str, expiration: int = 10):
    """Create a JWT bearer token for authenticating as a GitHub App"""

    time_since_epoch_in_seconds = int(time.time())

    payload = {
        # issued at time, 60 seconds in the past to allow for clock drift
        "iat": time_since_epoch_in_seconds - 60,
        # JWT expiration time (10 minute maximum)
        "exp": time_since_epoch_in_seconds + (expiration * 60),
        # GitHub App's identifier
        "iss": github_app_id,
    }

    encoded_payload = jwt.encode(payload, private_key, algorithm="RS256")
    return encoded_payload


def get_installation_id(jwt_bearer_token: str):
    """Returns the installation_id of a given github app"""

    headers = {
        "Authorization": f"Bearer {jwt_bearer_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    resp = requests.get(
        "https://api.github.com/app/installations", headers=headers, timeout=10
    )

    installation_id = json.loads(resp.content.decode())[0]["id"]
    return installation_id


def get_installation_access_token(installation_id: str, jwt_bearer_token: str):
    """Returns an Installation Access Token for a given installation_id"""

    headers = {
        "Authorization": f"Bearer {jwt_bearer_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    resp = requests.post(
        "https://api.github.com/app/installations/"
        + str(installation_id)
        + "/access_tokens",
        headers=headers,
        timeout=10,
    )

    installation_token = json.loads(resp.content.decode())["token"]
    return installation_token


if __name__ == "__main__":
    sys.exit(main())
