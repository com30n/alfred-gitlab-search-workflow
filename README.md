**Installation**

Just download `Gitlab.alfredworkflow` form the latest release:
https://github.com/com30n/alfred-gitlab-search-workflow/releases

**What problems it solves**`

This flow solves the problem with fast search in multiple repositories,
with their cloning, and rapid opening related links (like, commits, branches, pipelines, etc)

**Getting started with flow**

_Fist:_ setup environment variable `GIT_DIR`, which should specify path to your directory
which contains git projects.
_Second:_ you should generate api token in your gitlab, and then add new account to workflow
(you will need a gitlab url, a token name and the token).
_Third:_ when you add an gitlab account the workflow will download info about all repos from gitlab into local cache.

Now you can use the workflow!
