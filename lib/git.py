"Git helpers"

from subprocess import run, PIPE


def repo_version(repo):
    "Returns the version string for repo, unknown on errors"
    result = run(
        ["git", "describe", "--always", "--long", "--dirty", "--tags"],
        cwd=str(repo),
        stdout=PIPE,
        check=True,
    )
    git_ver = result.stdout.decode("utf-8").split("\n")[0]
    if git_ver:
        return git_ver
    return "unknown"
