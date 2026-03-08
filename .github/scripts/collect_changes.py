import requests
import os
from urllib.parse import quote
import logging

logger = logging.getLogger(__name__)


def sanitize_list_pull_request_files(
    gh_repo: str, owner: str, pull_request_id: str
) -> str:

    owner = owner.strip()
    if "/" in owner or " " in owner:
        raise ValueError("Invalid owner; should not contain '/' or whitespace")

    pr_str = str(pull_request_id).strip()
    if not pr_str.isdigit():
        raise ValueError("pull_request_id must be a number")

    if gh_repo:
        parts = gh_repo.split("/", 1)
        if len(parts) == 2:
            repo_name = parts[1]

    owner_quoted = quote(owner, safe="")
    repo_quoted = quote(repo_name, safe="")

    url = f"https://api.github.com/repos/{owner_quoted}/{repo_quoted}/pulls/{pr_str}/files"
    return url
    ...


def load_files() -> list[str]:
    """Retrieve the list of files changed in the current pull request.

    The GH action that invokes this script is expected to set the following
    environment variables:

    - ACTIONS_TOKEN: a personal access token or workflow token for the API
    - GITHUB_REPOSITORY: the owner/repo string for the current repository
    - PULL_REQUEST_ID: the pull request number being inspected

    """
    gh_actions_token = os.environ.get("ACTIONS_TOKEN")
    if not gh_actions_token:
        raise ValueError(
            "Could not get github actions token for API, please validate that it is set properly."
        )

    owner = os.environ.get("GITHUB_OWNER")
    pull_request_id = os.environ.get("PULL_REQUEST_ID")
    gh_repo = os.environ.get("GITHUB_REPOSITORY")

    if not owner or not pull_request_id or not gh_repo:
        raise ValueError(
            "All environment variables (GITHUB_OWNER, PULL_REQUEST_ID, GITHUB_REPOSITORY) must be set"
        )

    url = sanitize_list_pull_request_files(gh_repo, owner, pull_request_id)

    response = requests.get(url, headers={"Authorization": f"token {gh_actions_token}"})
    response.raise_for_status()
    files_list = []
    for entry in response.json():
        # each entry is a dict with a 'filename' key among others
        files_list.append(entry.get("filename"))

    return files_list


if __name__ == "__main__":
    load_files()
