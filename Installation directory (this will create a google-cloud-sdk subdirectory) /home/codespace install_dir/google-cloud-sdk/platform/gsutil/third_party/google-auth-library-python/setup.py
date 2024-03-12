# Copyright 2014 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import io
import os

from setuptools import find_packages
from setuptools import setup


DEPENDENCIES = (
    "cachetools>=2.0.0,<6.0",
    "pyasn1-modules>=0.2.1",
    # rsa==4.5 is the last version to support 2.7
    # https://github.com/sybrenstuvel/python-rsa/issues/152#issuecomment-643470233
    'rsa<4.6; python_version < "3.6"',
    'rsa>=3.1.4,<5; python_version >= "3.6"',
    # install enum34 to support 2.7. enum34 only works up to python version 3.3.
    'enum34>=1.1.10; python_version < "3.4"',
    "six>=1.9.0",
)

extras = {
    "aiohttp": [
        "aiohttp >= 3.6.2, < 4.0.0dev; python_version>='3.6'",
        "requests >= 2.20.0, < 3.0.0dev",
    ],
    "pyopenssl": ["pyopenssl>=20.0.0", "cryptography>=38.0.3"],
    "requests": "requests >= 2.20.0, < 3.0.0dev",
    "reauth": "pyu2f>=0.1.5",
    # Enterprise cert only works for OpenSSL 1.1.1. Newer versions of these
    # dependencies are built with OpenSSL 3.0 so we need to fix the version.
    "enterprise_cert": ["cryptography==36.0.2", "pyopenssl==22.0.0"],
}

with io.open("README.rst", "r") as fh:
    long_description = fh.read()

package_root = os.path.abspath(os.path.dirname(__file__))

version = {}
with open(os.path.join(package_root, "google/auth/version.py")) as fp:
    exec(fp.read(), version)
version = version["__version__"]

setup(
    name="google-auth",
    version=version,
    author="Google Cloud Platform",
    author_email="googleapis-packages@google.com",
    description="Google Authentication Library",
    long_description=long_description,
    url="https://github.com/googleapis/google-auth-library-python",
    packages=find_packages(exclude=("tests*", "system_tests*")),
    namespace_packages=("google",),
    install_requires=DEPENDENCIES,
    extras_require=extras,
    python_requires=">=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*,!=3.5.*",
    license="Apache 2.0",
    keywords="google auth oauth client",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: OS Independent",
        "Topic :: Internet :: WWW/HTTP",
    ],
)
