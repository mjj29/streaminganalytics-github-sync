EPL Apps Github sync
====================

This repository provides a tool to do bidirectional syncing between Github and Cumulocity Streaming Analytics EPL Apps.

To use this you will need a Cumulocity tenant with the ability to run EPL Apps, running at least Streaming Analytics 10.18.

To deploy it:

- Set the following tenant options in your tenant:
	- `github/owner` - The owner of the repository you want to sync to (the organization)
	- `github/repo` - The name of the repository in that organization you want to sync to
	- `github/branch` - The branch in the repository that you want to sync to
	- `github/PAT` - A Personal Access Token which has permissions to write to the repository
- Upload the contents of `syncapp/SyncToGithub.mon` to your tenant as an EPL App.

This will:

- Write all EPL Apps that exist at that moment in the tenant to the `epl/` directory of the github repository (overwriting any earlier versions in the repository)
- Deploy any already-existing Apps under `epl/` from the github repository to the tenant as new EPL Apps
- Watch for updates to EPL Apps going forward and write any changes / remove any deleted EPL Apps from the github repository
- Watch for new commits to the github repository and make any changes to match in EPL Apps

You can use this to implement the following use cases and more:

- Backup your EPL Apps to github, with tracked changes
- Restore your EPL Apps to a new blank tenant
- Develop your EPL Apps outside of EPL Apps with standard enterprise workflows, including testing using eplapps-tools, but automatically have them deployed to your tenant
- Develop in one tenant on one branch, have preprod and production in other tenants connected to other branches and do release between them with pull requests in github 

This repo contains:

- `syncapp/SyncToGithub.mon` - The EPL App which will do the syncing
- `tests/` - Test cases for syncing

To run the tests you will need:

- `eplapps-tools` from https://github.com/SoftwareAG/apama-eplapps-tools
- `pysys` from https://github.com/pysys-test/pysys-test or from an installation of Software AG Apama
- Set the following environment variables:
	- `CUMULOCITY_SERVER_URL` - the address of your tenant
	- `CUMULOCITY_USERNAME` - the username to access the tenant
	- `CUMULOCITY_PASSWORD` - the password to access the tenant
	- `GITHUB_REPO` - the owner/repo that you want to sync to in github
	- `GITHUB_ACCESS_TOKEN` - a Personal Access Token which has permissions to write to the repository
	- `GIT_BRANCH` - the branch to write to in the repository
	- `EPL_TESTING_SDK` - the path to the eplapps-tools checkout
- run `pysys run` in the tests directory.

*WARNING: Running the test will modify and potentially delete the contents of your tenant and your repository.*
