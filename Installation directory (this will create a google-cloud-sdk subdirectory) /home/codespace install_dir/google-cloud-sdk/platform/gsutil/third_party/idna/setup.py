"""
A library to support the Internationalised Domain Names in Applications
(IDNA) protocol as specified in RFC 5890 et.al. This new methodology,
known as IDNA 2008, can generate materially different results to the
previous standard. The library can act as a drop-in replacement for
the "encodings.idna" module.
"""

import io, sys
from setuptools import setup


def main():

    python_version = sys.version_info[:2]
    if python_version < (3,4):
        raise SystemExit("Sorry, Python 3.4 or newer required")

    package_data = {}
    exec(open('idna/package_data.py').read(), package_data)

    arguments = {
        'name': 'idna',
        'packages': ['idna'],
        'package_data': {'idna': ['py.typed']},
        'include_package_data': True,
        'version': package_data['__version__'],
        'description': 'Internationalized Domain Names in Applications (IDNA)',
        'long_description': open("README.rst", encoding="UTF-8").read(),
        'author': 'Kim Davies',
        'author_email': 'kim@cynosure.com.au',
        'license': 'BSD-3-Clause',
        'url': 'https://github.com/kjd/idna',
        'classifiers': [
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Developers',
            'Intended Audience :: System Administrators',
            'License :: OSI Approved :: BSD License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3 :: Only',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Programming Language :: Python :: Implementation :: CPython',
            'Programming Language :: Python :: Implementation :: PyPy',
            'Topic :: Internet :: Name Service (DNS)',
            'Topic :: Software Development :: Libraries :: Python Modules',
            'Topic :: Utilities',
        ],
        'python_requires': '>=3.5',
        'test_suite': 'tests',
    }

    setup(**arguments)

if __name__ == '__main__':
    main()
