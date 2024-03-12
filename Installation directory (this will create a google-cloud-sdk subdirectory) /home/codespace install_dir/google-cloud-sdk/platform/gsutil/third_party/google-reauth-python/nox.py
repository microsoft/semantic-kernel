# Copyright 2016 Google
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import

import nox


@nox.session
@nox.parametrize('py', ['2.7', '3.4'])
def tests(session, py):
    session.interpreter = 'python{}'.format(py)
    session.install('mock', 'pytest', 'pytest-cov')
    session.install('-e', '.[oauth2client]')

    session.run(
        'py.test',
        '--quiet',
        '--cov=google_reauth',
        '--cov-config=.coveragerc',
        'tests',
        *session.posargs
    )


@nox.session
def lint(session):
    session.install('flake8', 'docutils', 'pygments')
    session.run('flake8', 'google_reauth')
    session.run(
        'python', 'setup.py', 'check', '--restructuredtext', '--strict')
