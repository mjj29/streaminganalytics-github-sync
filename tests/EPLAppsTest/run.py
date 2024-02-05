# Sample PySys testcase

# Copyright (c) 2020 Software AG, Darmstadt, Germany and/or its licensors

# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this
# file except in compliance with the License. You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the
# License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

from pysys.constants import *
from apamax.eplapplications import CumulocityPlatform, EPLApps
from apamax.eplapplications.basetest import ApamaC8YBaseTest
import os, re, github, time, base64

class PySysTest(ApamaC8YBaseTest):

	def waitForGithubFile(self, repo, dir, file, exists=True, timeout=120, errExpr=None, errFile=None):
		print(f"Waiting for {file} in {dir} to {'exist' if exists else 'not exist'}", end='', flush=True)
		totaltime = 0
		while exists != (file in str(repo.get_contents(dir))):
			if errExpr and errFile:
				for expr in errExpr:
					result = self.grepOrNone(errFile, expr=expr)
					if result:
						self.abort(BLOCKED, "Found error while waiting for github file to exist: %s"%result)
			time.sleep(5)
			totaltime = totaltime + 5
			if totaltime > timeout:
				print(" failed, current contents is: %s"%str(repo.get_contents(dir)))
				self.abort(TIMEDOUT, "Timed out waiting for github file to exist")
			print(".", end='', flush=True)
		print(" done")
	
	def waitForGithubContent(self, repo, dir, file, content, timeout=120, errExpr=None, errFile=None):
		# first ensure the file exists
		self.waitForGithubFile(repo, dir, file, timeout=timeout, errExpr=errExpr, errFile=errFile)
		# then check the contents against the argument
		print(f"Waiting for {file} in {dir} content to match {content}", end='', flush=True)
		totaltime = 0
		while not re.search(content, base64.b64decode(repo.get_contents(f"{dir}/{file}").content).decode("ascii")):
			if errExpr and errFile:
				for expr in errExpr:
					result = self.grepOrNone(errFile, expr=expr)
					if result:
						self.abort(BLOCKED, "Found error while waiting for github content: %s"%result)
			time.sleep(5)
			totaltime = totaltime + 5
			if totaltime > timeout:
				print(" failed, current contents is: %s" % base64.b64decode(repo.get_contents(f"{dir}/{file}").content).decode("ascii"))
				self.abort(TIMEDOUT, "Timed out waiting for github content")
			print(".", end='', flush=True)
		print(" done")

	def cleanupTest(self, eplapps, repo):
		try:
			apps = eplapps.getEPLApps()
			for a in ['SyncToGithub', 'PYSYS_Test01', 'PYSYS_Test02']:
				for app in apps:
					if a in app['name']:
						print("Deleting app "+app['name'])
						eplapps.delete(name=app['name'])
		except Exception as e:
			print("Ignoring exception in cleaning epl apps: %s"%e)
		
		try:
			contents = repo.get_contents('epl')
			for a in ['PYSYS_Test01', 'PYSYS_Test02', 'SyncToGithub']:
				for c in contents:
					if a in c.path:
						print("Deleting from github "+c.path)
						repo.delete_file(c.path, "Remove "+c.path+" for test cleanup", c.sha, branch=self.project.GIT_BRANCH)
		except Exception as e:
			print("Ignoring exception in cleaning github: %s"%e)




	def execute(self):

		self.log.info(f"Running test with tenant {self.project.CUMULOCITY_SERVER_URL} user {self.project.CUMULOCITY_USERNAME} and github repo {self.project.GITHUB_API_URL}/repos/{self.project.GITHUB_REPO} branch {self.project.GIT_BRANCH}")

		errs=[' ERROR .* SyncToGithub.GitHandlerMonitor']
		g = github.Github(base_url=self.project.GITHUB_API_URL, auth=github.Auth.Token(self.project.GITHUB_ACCESS_TOKEN))
		repo = g.get_repo(self.project.GITHUB_REPO)

		connection = self.platform.getC8YConnection()
		eplapps = EPLApps(connection)
		self.cleanupTest(eplapps, repo)

		# configure the tenant options
		for (option, value) in [
				("streaminganalytics.github/PAT", self.project.GITHUB_ACCESS_TOKEN),
				("streaminganalytics.github/branch", self.project.GIT_BRANCH),
				("streaminganalytics.github/owner", self.project.GITHUB_REPO.split('/')[0]),
				("streaminganalytics.github/repo", self.project.GITHUB_REPO.split('/')[1]),
				("streaminganalytics.github/githubAPIURL", self.project.GITHUB_API_URL),
		]:
			self.log.info(f"Setting tenant option {option} to {'*********' if 'PAT' in option else value}")
			connection.request("PUT", "/tenant/options/"+option, '{"value":"'+value+'"}', {"content-type":"application/json"})

		# deploy the sync app
		eplapps.deploy(os.path.join(self.project.EPL_APPS, "SyncToGithub.mon"), name='SyncToGithub', redeploy=True, description='Github sync app, injected by test framework')
		self.waitForGrep(self.platform.getApamaLogFile(), expr='eplfiles.SyncToGithub.GitHandlerMonitor .[0-9]*. Synchronizing EPL Apps', errorExpr=errs)
		self.wait(10)

		# deploy the test
		eplapps.deploy(os.path.join(self.input, 'AlarmOnMeasurementThresholdTest.mon'), name='PYSYS_Test01', description='Test case, injected by test framework', redeploy=True)
		self.waitForGrep(self.platform.getApamaLogFile(), expr='EPL Apps updated EPL File.*PYSYS_Test01', errorExpr=errs)
		self.waitForGrep(self.platform.getApamaLogFile(), expr='Updating file state in git for PYSYS_Test01', errorExpr=errs)
		self.waitForGithubFile(repo, 'epl', 'PYSYS_Test01.state', errFile=self.platform.getApamaLogFile(), errExpr=errs)
		self.waitForGithubContent(repo, 'epl', 'PYSYS_Test01.state', 'active', errFile=self.platform.getApamaLogFile(), errExpr=errs)
		self.waitForGithubContent(repo, 'epl', 'PYSYS_Test01.txt', 'Test case, injected by test framework', errFile=self.platform.getApamaLogFile(), errExpr=errs)
		self.waitForGithubContent(repo, 'epl', 'PYSYS_Test01.mon', 'Created Test1', errFile=self.platform.getApamaLogFile(), errExpr=errs)
		self.wait(10)

		# redeploy no change
		eplapps.deploy(os.path.join(self.input, 'AlarmOnMeasurementThresholdTest.mon'), name='PYSYS_Test01', description='Test case, injected by test framework', redeploy=True)
		self.waitForGrep(self.platform.getApamaLogFile(), expr='EPL Apps updated EPL File.*PYSYS_Test01', errorExpr=errs)
		self.wait(10)

		# redeploy with change
		eplapps.deploy(os.path.join(self.input, 'AlarmOnMeasurementThresholdTest2.mon'), name='PYSYS_Test01', description='Test case, injected by test framework', redeploy=True)
		self.waitForGrep(self.platform.getApamaLogFile(), expr='EPL Apps updated EPL File.*PYSYS_Test01', errorExpr=errs)
		self.waitForGithubContent(repo, 'epl', 'PYSYS_Test01.mon', 'Created Test2', errFile=self.platform.getApamaLogFile(), errExpr=errs)
		self.wait(10)

		# deactivate
		eplapps.update(name='PYSYS_Test01', state='inactive')
		self.waitForGrep(self.platform.getApamaLogFile(), expr='EPL Apps updated EPL File.*PYSYS_Test01', errorExpr=errs)
		self.waitForGithubContent(repo, 'epl', 'PYSYS_Test01.state', 'inactive', errFile=self.platform.getApamaLogFile(), errExpr=errs)
		self.wait(10)

		# activate
		eplapps.update(name='PYSYS_Test01', state='active')
		self.waitForGrep(self.platform.getApamaLogFile(), expr='EPL Apps updated EPL File.*PYSYS_Test01', errorExpr=errs)
		self.waitForGithubContent(repo, 'epl', 'PYSYS_Test01.state', 'active', errFile=self.platform.getApamaLogFile(), errExpr=errs)
		self.wait(10)

		# delete
		eplapps.delete(name='PYSYS_Test01')
		self.waitForGithubFile(repo, 'epl', 'PYSYS_Test01.state', exists=False, errFile=self.platform.getApamaLogFile(), errExpr=errs)
		self.wait(10)

		# add via github (inactive)
		self.log.info("Creating PYSYS_Test02 in github")
		descriptionfile = repo.create_file("epl/PYSYS_Test02.txt", "Add PYSYS_Test02 description", "PYSYS_Test02 description", branch=self.project.GIT_BRANCH)
		self.waitForGithubFile(repo, 'epl', 'PYSYS_Test02.txt', errFile=self.platform.getApamaLogFile(), errExpr=errs)
		statefile = repo.create_file("epl/PYSYS_Test02.state", "Add PYSYS_Test02 state", "inactive", branch=self.project.GIT_BRANCH)
		self.waitForGithubFile(repo, 'epl', 'PYSYS_Test02.state', errFile=self.platform.getApamaLogFile(), errExpr=errs)
		monitorfile = repo.create_file("epl/PYSYS_Test02.mon", "Add PYSYS_Test02 contents", 'monitor PYSYS_Test02 { action onload() { log "Loaded PYSYS_Test02"; on all any() {} } }', branch=self.project.GIT_BRANCH)
		self.waitForGithubFile(repo, 'epl', 'PYSYS_Test02.mon', errFile=self.platform.getApamaLogFile(), errExpr=errs)
		for expr in [
				f"Checking new commit ({monitorfile['commit'].sha}|{statefile['commit'].sha}|{descriptionfile['commit'].sha}) for changes to EPL Apps",
				"Updating EPL app PYSYS_Test02 in C8Y",
		]:
			self.waitForGrep(self.platform.getApamaLogFile(), expr=expr, errorExpr=errs)
		self.wait(10)

		# activate via github
		self.log.info("Activating PYSYS_Test02 in github")
		statefile = repo.update_file(statefile['content'].path, "Update PYSYS_Test02 state", "active", repo.get_contents(statefile['content'].path).sha, branch=self.project.GIT_BRANCH)
		for expr in [
				f"Checking new commit {statefile['commit'].sha} for changes to EPL Apps",
				"Updating EPL app PYSYS_Test02 in C8Y",
				"eplfiles.PYSYS_Test02.PYSYS_Test02.*Loaded PYSYS_Test02",
		]:
			self.waitForGrep(self.platform.getApamaLogFile(), expr=expr, errorExpr=errs)
		self.wait(10)


		# edit via github
		self.log.info("Updating PYSYS_Test02 in github")
		monitorfile = repo.update_file(monitorfile['content'].path, "Update PYSYS_Test02 content", 'monitor PYSYS_Test02 { action onload() { log "Loaded Updated PYSYS_Test02"; on all any() {} } }', repo.get_contents(monitorfile['content'].path).sha, branch=self.project.GIT_BRANCH)
		for expr in [
				f"Checking new commit {monitorfile['commit'].sha} for changes to EPL Apps",
				"Updating EPL app PYSYS_Test02 in C8Y",
				"eplfiles.PYSYS_Test02.PYSYS_Test02.*Loaded Updated PYSYS_Test02",
		]:
			self.waitForGrep(self.platform.getApamaLogFile(), expr=expr, errorExpr=errs)
		self.wait(10)

		# remove via github
		self.log.info("Deleting PYSYS_Test02 in github")
		delmon = repo.delete_file(monitorfile['content'].path, "Remove PYSYS_Test02 contents", repo.get_contents(monitorfile['content'].path).sha, branch=self.project.GIT_BRANCH)
		delstate = repo.delete_file(statefile['content'].path, "Remove PYSYS_Test02 state", repo.get_contents(statefile['content'].path).sha, branch=self.project.GIT_BRANCH)
		deldescr = repo.delete_file(descriptionfile['content'].path, "Remove PYSYS_Test02 description", repo.get_contents(descriptionfile['content'].path).sha, branch=self.project.GIT_BRANCH)
		for expr in [
				f"Checking new commit ({delmon['commit'].sha}|{delstate['commit'].sha}|{deldescr['commit'].sha}) for changes to EPL Apps",
		]:
			self.waitForGrep(self.platform.getApamaLogFile(), expr=expr, errorExpr=errs)


		self.cleanupTest(eplapps, repo)

	def validate(self):
		# check none of the tests failed
		self.assertGrep(self.platform.getApamaLogFile(), expr=' (ERROR|FATAL) .* eplfiles\.', contains=False)
		




