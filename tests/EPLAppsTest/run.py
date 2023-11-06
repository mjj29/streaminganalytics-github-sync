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
import os 
import github
import time

class PySysTest(ApamaC8YBaseTest):

	def waitForGithubFile(self, repo, dir, file, exists=True):
		print(f"Waiting for {file} in {dir} to {'exist' if exists else 'not exist'}", end='', flush=True)
		while exists != file in str(repo.get_contents(dir)):
			time.sleep(1)
			print(".", end='', flush=True)
		print("done")

	def execute(self):

		errs=[' ERROR .* SyncToGithub.GitHandlerMonitor']
		g = github.Github()
		repo = g.get_repo("mjj29/epl-apps-test-sync-target")

		# connect to the platform
		self.platform = CumulocityPlatform(self)
		eplapps = EPLApps(self.platform.getC8YConnection())
		# start clean
		apps = eplapps.getEPLApps()
		for a in ['PYSYS_Test01', 'SyncToGithub']:
			if a in apps:
				eplapps.delete(name=a)

		# deploy the sync app
		eplapps.deploy(os.path.join(self.project.EPL_APPS, "SyncToGithub.mon"), name='SyncToGithub', redeploy=True, description='Github sync app, injected by test framework')
		self.waitForGrep(self.platform.getApamaLogFile(), expr='eplfiles.SyncToGithub.GitHandlerMonitor .[0-9]*. Synchronizing EPL Apps', errorExpr=errs)
		print(str(repo.get_contents("epl")))

		# deploy the test
		eplapps.deploy(os.path.join(self.input, 'AlarmOnMeasurementThresholdTest.mon'), name='PYSYS_Test01', description='Test case, injected by test framework', redeploy=True)
		self.waitForGrep(self.platform.getApamaLogFile(), expr='EPL Apps updated EPL File.*PYSYS_Test01', errorExpr=errs)
		self.waitForGrep(self.platform.getApamaLogFile(), expr='Updating file state in git for PYSYS_Test01', errorExpr=errs)
		self.waitForGithubFile(repo, 'epl', 'PYSYS_Test01.state')
		print(str(repo.get_contents("epl/PYSYS_Test01.state")))

		# delete
		eplapps.delete(name='PYSYS_Test01')
		self.waitForGithubFile(repo, 'epl', 'PYSYS_Test01.state', exists=False)

		return

		# redeploy no change
		eplapps.deploy(os.path.join(self.input, 'AlarmOnMeasurementThresholdTest.mon'), name='PYSYS_Test01', description='Test case, injected by test framework', redeploy=True)
		self.waitForGrep(self.platform.getApamaLogFile(), expr='EPL Apps updated EPL File.*PYSYS_Test01', errorExpr=errs)

		# redeploy with change
		eplapps.deploy(os.path.join(self.input, 'AlarmOnMeasurementThresholdTest2.mon'), name='PYSYS_Test01', description='Test case, injected by test framework', redeploy=True)
		self.waitForGrep(self.platform.getApamaLogFile(), expr='EPL Apps updated EPL File.*PYSYS_Test01', errorExpr=errs)

		# deactivate
		eplapps.update(name='PYSYS_Test01', state='inactive')
		self.waitForGrep(self.platform.getApamaLogFile(), expr='EPL Apps updated EPL File.*PYSYS_Test01', errorExpr=errs)

		# activate
		eplapps.update(name='PYSYS_Test01', state='active')
		self.waitForGrep(self.platform.getApamaLogFile(), expr='EPL Apps updated EPL File.*PYSYS_Test01', errorExpr=errs)

		self.waitForGrep(self.platform.getApamaLogFile(), expr='EPL Apps updated EPL File.*PYSYS_Test01', errorExpr=errs)

		# add via github (inactive)
		# activate via github
		# edit via github
		# remove via github

	def validate(self):
		# check none of the tests failed
		self.assertGrep(self.platform.getApamaLogFile(), expr=' (ERROR|FATAL) .* eplfiles\.', contains=False)
		




