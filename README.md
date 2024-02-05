EPL Apps GitHub sync
====================

This repository provides a tool to do bidirectional syncing between GitHub and Cumulocity Streaming Analytics EPL apps.

To use this you will need a Cumulocity tenant with the ability to run EPL apps, running at least Streaming Analytics 10.18.0.5, or any CD train (versions starting 24+).

To deploy it:

- Set the following tenant options in your tenant:
	- `streaminganalytics.github/owner` - The owner of the repository you want to sync to (the organization)
	- `streaminganalytics.github/repo` - The name of the repository in that organization you want to sync to
	- `streaminganalytics.github/branch` - The branch in the repository that you want to sync to
	- `streaminganalytics.github/PAT` - A Personal Access Token which has permissions to write to the repository
	- `streaminganalytics.github/githubAPIURL` - Optionally, if this repository is not hosted on github.com, override the URL to the github API endpoint
- Upload the contents of `syncapp/SyncToGithub.mon` to your tenant as an EPL App.

This will:

- Write all EPL apps that exist at that moment in the tenant to the `epl/` directory of the GitHub repository (overwriting any earlier versions in the repository)
- Deploy any already-existing Apps under `epl/` from the GitHub repository to the tenant as new EPL apps
- Watch for updates to EPL apps going forward and write any changes / remove any deleted EPL apps from the GitHub repository
- Watch for new commits to the GitHub repository and make any changes to match in EPL apps

Note that the github repository will need to already exist and be initialized.

You can use this to implement the following use cases and more:

- Backup your EPL apps to GitHub, with tracked changes
- Restore your EPL apps to a new blank tenant
- Develop your EPL apps outside of EPL apps with standard enterprise workflows, including testing using eplapps-tools, but automatically have them deployed to your tenant
- Develop in one tenant on one branch, have preprod and production in other tenants connected to other branches and do release between them with pull requests in GitHub 

This repo contains:

- `syncapp/SyncToGithub.mon` - The EPL App which will do the syncing
- `tests/` - Test cases for syncing

To run the tests you will need:

- `eplapps-tools` from https://github.com/SoftwareAG/apama-eplapps-tools
- `pysys` from https://github.com/pysys-test/pysys-test or from an installation of Software AG Apama
- Install `pygithub` in your python environment
- Set the following environment variables:
	- `CUMULOCITY_SERVER_URL` - the address of your tenant
	- `CUMULOCITY_USERNAME` - the username to access the tenant
	- `CUMULOCITY_PASSWORD` - the password to access the tenant
	- `GITHUB_REPO` - the owner/repo that you want to sync to in GitHub
	- `GITHUB_ACCESS_TOKEN` - a Personal Access Token which has permissions to write to the repository
	- `GIT_BRANCH` - the branch to write to in the repository
	- `EPL_TESTING_SDK` - the path to the eplapps-tools checkout
- run `pysys run` in the tests directory.

*WARNING: Running the test will modify and potentially delete the contents of your tenant and your repository.*

LICENSE
-------

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this 
file except in compliance with the License. You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software distributed under the
License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, 
either express or implied. 
See the License for the specific language governing permissions and limitations under the License.
