from distutils.core import setup
from distutils.extension import Extension
import sys,os

if sys.version_info[0] == 2:
    base_dir = 'python2'
elif sys.version_info[0] == 3:
    base_dir = 'python3'

setup_dict = dict(
name='crcmod',
version='1.7',
description='CRC Generator',
author='Ray Buvel',
author_email='rlbuvel@gmail.com',
url='http://crcmod.sourceforge.net/',
download_url='http://sourceforge.net/projects/crcmod',
packages=['crcmod'],
package_dir={
    'crcmod' : os.path.join(base_dir,'crcmod'),
},

ext_modules=[ 
    Extension('crcmod._crcfunext', [os.path.join(base_dir,'src/_crcfunext.c'), ],
    ),
],

long_description=open('README').read(),

license="MIT",
classifiers=[
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'Intended Audience :: Education',
    'Intended Audience :: End Users/Desktop',
    'Intended Audience :: Information Technology',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: C',
    'Programming Language :: C++',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.4',
    'Programming Language :: Python :: 2.5',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.1',
    'Topic :: Communications',
    'Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator',
    'Topic :: Scientific/Engineering :: Mathematics',
    'Topic :: Utilities',
],
)

try:
    setup(**setup_dict)
except KeyboardInterrupt:
    raise
except:
    # If there are any compilation errors or there are no build tools available
    # for the extension module, delete the extension module and try to install
    # the pure Python version.
    del setup_dict['ext_modules']
    setup(**setup_dict)
