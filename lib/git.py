"Git helpers"

from subprocess import run, CalledProcessError, PIPE


def repo_version(repo):
    "Returns the version string for repo, unknown on errors"
    try:
        result = run(
            ["git", "describe", "--always", "--long", "--dirty", "--tags"],
            cwd=str(repo),
            stdout=PIPE,
            check=True,
        )
        return result.stdout.decode("utf-8").split("\n")[0]
    except CalledProcessError:
        return "unknown"
