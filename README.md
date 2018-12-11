# git-cog.py

A small git extension for github, gitlab
written in Python3 and relying on

- Github API v3
- GitLab API v4

## Install

clone and add this to your path.
`pip install -r requirements.txt` as well

## Usage

### create a pull request

```
git cog create-pullrequest <remote> [--into <master>] [--head <current branch>] [--title <title>] [--message <message>]
```

### find pull requests

```
git cog find-pullrequests <remote> [--into <master>] [--head <current branch>]
```

### more functionality to be added over time

## Configuration

The follwing configuration entries must be st (either global or local):

```
[cog "github/gitlab domain"]
	token = your token
	api = gitlab | github
```

The tool will to try to match the correct configuration entries with the given remote

Example:

```
[cog "github.com"]
	token = token123token123token123token123token123
	api = github
[cog "github.enterprise.tld"]
	token = token123token123token123token123token123
	api = github
[cog "gitlab.com"]
	token = token123token123
	api = gitlab
```

## Example

```
git cog create-pullrequest origin --into master --head feature/cookies -t "merging cookies" -m "hmm! cookies!!"
```
