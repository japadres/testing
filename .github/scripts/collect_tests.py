import requests
import os
from urllib.parse import quote
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def sanitize_list_pull_request_files(
    gh_repo: str, owner: str, pull_request_id: str
) -> str:
    """Sanitizes the inputs and constructs the GitHub API URL to list files in a pull request.

    Args:
        gh_repo (str): The GitHub repository in the format "owner/repo".
        owner (str): The owner of the repository.
        pull_request_id (str): The ID of the pull request.

    Raises:
        ValueError: If the owner is invalid, pull_request_id is not a number, or required environment variables are missing.
        ValueError: If the repository string is not in the expected format.

    Returns:
        str: The sanitized URL to list files in the pull request.
    """

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
    """Loads the list of changed files from the GitHub API.

    Raises:
        ValueError: If required environment variables are missing or invalid.
        requests.RequestException: If the API request fails.

    Returns:
        list[str]: A list of filenames that were changed in the pull request.
    """
    gh_actions_token = os.environ.get("GITHUB_TOKEN")
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
        logger.info(f"Found changed file: {entry.get('filename')}")
        files_list.append(entry.get("filename"))

    return files_list


def write_test_files(files: list[str]) -> None:
    """Writes the list of test files to the GitHub Actions output file for the workflow to consume.

    Args:
        files (list[str]): The list of test files to write to the output.

    Raises:
        ValueError: If the GITHUB_OUTPUT environment variable is not set.
    """
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        raise ValueError(
            "GITHUB_OUTPUT environment variable is not set; cannot write output"
        )
    with open(output_path, "w") as fh:
        for f in files:
            fh.write("files<<EOF\n")
            fh.write("\n".join(files))
            fh.write("\nEOF\n")


def _collect_project_test_files(project: str) -> list[str]:
    """Collects the test files for a specific project.

    Args:
        project (str): The project for which to collect test files.

    Returns:
        list[str]: The list of test files for the specified project.
    """
    project_path = Path(project)
    test_files = [str(p) for p in project_path.glob("**/test_*.py") if p.is_file()]

    return test_files


def collect_test_files(files: list[str]) -> list[str]:
    """Collects the test files related to the changed projects or if a change is to common then checks all tests.

    Args:
        files (list[str]): The list of changed files in the pull request.

    Returns:
        list[str]: The list of test files to run based on the changed files.
    """
    githunb_workspace = os.environ.get("GITHUB_WORKSPACE")
    if not githunb_workspace:
        raise ValueError(
            "GITHUB_WORKSPACE environment variable is not set; cannot determine test file paths"
        )

    test_watch_files = os.environ.get("WATCH_FILES")
    if not test_watch_files:
        raise ValueError("WATCH_FILES environment variable is not set; ")
    test_watch_files = [
        wf.strip() for wf in test_watch_files.split(",") if wf not in ("", None)
    ]
    test_files = []
    projects = set()
    for file in files:
        if file:
            file_path = Path(file)
            parents = file_path.parents
            project = f"{parents[0]}/{parents[1]}" if len(parents) > 1 else None
            if not project:
                logger.warning(f"Could not determine project for file {file}, skipping")
                continue
            elif "common" in parents and file_path.suffix in test_watch_files:
                test_files.extend(_collect_project_test_files(githunb_workspace))
                break
            elif file_path.suffix in test_watch_files and project not in projects:
                project_with_workspace = f"{githunb_workspace}/{project}"
                project_test_file = _collect_project_test_files(project_with_workspace)
                test_files.extend(project_test_file)
                projects.add(project)

    return test_files


def collect_tests() -> None:
    """Colelcts the tests impacted by the changed files and writes them to the output path for the workflow to consume."""
    files = load_files()
    test_files = collect_test_files(files)
    write_test_files(test_files)


if __name__ == "__main__":
    collect_tests()
