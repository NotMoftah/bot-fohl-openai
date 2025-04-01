import os
import sys
import json
import requests


# region: env variables and static strings
ENV_GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
ENV_REPO_NAME = os.environ["REPO_NAME"]
ENV_PR_NUMBER = os.environ["PR_NUMBER"]
ENV_PR_DESCRIPTION = os.getenv("PR_DESCRIPTION", "")
COMMENT_THANK_YOU = (
    "Thank you for your pull request! We will review it as soon as possible."
)


# region: functions
def exit_based_on_state(is_success_state: bool) -> None:
    """
    Exits with code 0 if the is_success_state is True, indicating success.
    Exits with code 1 if the is_success_state is False, indicating failure.

    Parameters:
    - is_success_state: A boolean indicating the state to check.

    Returns: None
    """
    exit_code = 0 if is_success_state else 1
    sys.exit(exit_code)


def post_github_comment(
    repo_name: str, pr_number: int, token: str, comment_body: str
) -> None:
    """
    Posts a comment to a GitHub pull request.

    Parameters:
    - repo_name: The name of the repository (format "owner/repo").
    - pr_number: The number of the pull request.
    - token: The GitHub API token for authentication.
    - comment_body: The body of the comment to post.

    Returns: None
    """
    url = f"https://api.github.com/repos/{repo_name}/issues/{pr_number}/comments"
    headers = {"Authorization": f"token {token}", "Content-Type": "application/json"}
    data = {"body": comment_body}
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 201:
        print("Comment posted successfully.")
    else:
        print(response.status_code)
        print(response.text)


# region: entry point
if __name__ == "__main__":
    post_github_comment(
        ENV_REPO_NAME, ENV_PR_NUMBER, ENV_GITHUB_TOKEN, COMMENT_THANK_YOU
    )
    exit_based_on_state(True)
