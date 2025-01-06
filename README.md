# Pulling changes from class engine repo

To clone a public Git repository into your private repository while maintaining the ability to pull updates (e.g., bug fixes) from the public repository, you can use the following steps:

1. Clone the Public Repository
Start by cloning the public repository locally:

git clone https://github.com/public/repo.git
This will create a local copy of the public repository.

2. Add Your Private Repository as a New Remote
Navigate to the local clone of the public repository:

cd repo
Add your private repository as a new remote:

git remote add private https://github.com/yourusername/private-repo.git
Verify the remotes to ensure both are set up:

git remote -v
You should see both origin (the public repo) and private (your private repo).

3. Push the Public Repo's Contents to Your Private Repo
Push the contents to your private repository. If the private repository is empty, you can use the following:

git push private main
(Replace main with the appropriate branch name if it differs.)

4. Sync Updates from the Public Repository
Whenever there are updates in the public repository, you can fetch and merge them into your private repository:

Fetch updates from the public repository:
git fetch origin
Merge the updates into your local branch:
git merge origin/main
(Replace main with the branch name if necessary.)
Push the merged changes to your private repository:
git push private main
5. Automate Keeping Your Private Repo Updated
You can automate this process using a script if frequent syncing is required. Here's an example:

#!/bin/bash
## Pull updates from the public repository
git fetch origin
git merge origin/main

## Push updates to the private repository
git push private main
Save the script, make it executable (chmod +x script.sh), and run it periodically.

Notes:
If there are conflicts during the merge process, you will need to resolve them manually.
Make sure the private repository is accessible only to authorized users to protect its contents.


# Dependencies
 - python>=3.5
 - cython (pip install cython)
 - eval7 (pip install eval7)
 - Java>=8 for java_skeleton
 - C++17 for cpp_skeleton
 - boost for cpp_skeleton (`sudo apt install libboost-all-dev`)

## Linting
Use pylint.
