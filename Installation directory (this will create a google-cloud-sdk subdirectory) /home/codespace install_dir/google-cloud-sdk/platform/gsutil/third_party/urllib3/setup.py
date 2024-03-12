#!/usr/bin/env python
# This file is protected via CODEOWNERS

import codecs
import os
import re

from setuptools import setup

base_path = os.path.dirname(__file__)

# Get the version (borrowed from SQLAlchemy)
with open(os.path.join(base_path, "src", "urllib3", "_version.py")) as fp:
    VERSION = (
        re.compile(r""".*__version__ = ["'](.*?)['"]""", re.S).match(fp.read()).group(1)
    )


with codecs.open("README.rst", encoding="utf-8") as fp:
    # Remove reST raw directive from README as they're not allowed on PyPI
    # Those blocks start with a newline and continue until the next newline
    mode = None
    lines = []
    for line in fp:
        if line.startswith(".. raw::"):
            mode = "ignore_nl"
        elif line == "\n":
            mode = "wait_nl" if mode == "ignore_nl" else None

        if mode is None:
            lines.append(line)
    readme = "".join(lines)

with codecs.open("CHANGES.rst", encoding="utf-8") as fp:
    changes = fp.read()

version = VERSION

setup(
    name="urllib3",
    version=version,
    description="HTTP library with thread-safe connection pooling, file post, and more.",
    long_description=u"\n\n".join([readme, changes]),
    long_description_content_type="text/x-rst",
    classifiers=[
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries",
    ],
    keywords="urllib httplib threadsafe filepost http https ssl pooling",
    author="Andrey Petrov",
    author_email="andrey.petrov@shazow.net",
    url="https://urllib3.readthedocs.io/",
    project_urls={
        "Documentation": "https://urllib3.readthedocs.io/",
        "Code": "https://github.com/urllib3/urllib3",
        "Issue tracker": "https://github.com/urllib3/urllib3/issues",
    },
    license="MIT",
    packages=[
        "urllib3",
        "urllib3.packages",
        "urllib3.packages.backports",
        "urllib3.contrib",
        "urllib3.contrib._securetransport",
        "urllib3.util",
    ],
    package_dir={"": "src"},
    requires=[],
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, <4",
    extras_require={
        "brotli": [
            "brotli>=1.0.9; (os_name != 'nt' or python_version >= '3') and platform_python_implementation == 'CPython'",
            "brotlicffi>=0.8.0; (os_name != 'nt' or python_version >= '3') and platform_python_implementation != 'CPython'",
            "brotlipy>=0.6.0; os_name == 'nt' and python_version < '3'",
        ],
        "secure": [
            "pyOpenSSL>=0.14",
            "cryptography>=1.3.4",
            "idna>=2.0.0",
            "certifi",
            "ipaddress; python_version=='2.7'",
        ],
        "socks": ["PySocks>=1.5.6,<2.0,!=1.5.7"],
    },
)
