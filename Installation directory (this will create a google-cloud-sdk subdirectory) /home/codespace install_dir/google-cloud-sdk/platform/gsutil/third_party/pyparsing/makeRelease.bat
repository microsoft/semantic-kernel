copy ..\sourceforge\svn\trunk\src\CHANGES .
copy ..\sourceforge\svn\trunk\src\setup.py .
copy ..\sourceforge\svn\trunk\src\pyparsing.py .
copy ..\sourceforge\svn\trunk\src\MANIFEST.in_bdist .
copy ..\sourceforge\svn\trunk\src\MANIFEST.in_src .
copy ..\sourceforge\svn\trunk\src\examples\* .\examples\

rmdir build
rmdir dist

copy/y MANIFEST.in_src MANIFEST.in
if exist MANIFEST del MANIFEST
python setup.py sdist --formats=gztar,zip

copy/y MANIFEST.in_bdist MANIFEST.in
if exist MANIFEST del MANIFEST

python setup.py bdist_wheel
python setup.py bdist_wininst --target-version=2.6 --plat-name=win32
python setup.py bdist_wininst --target-version=2.7 --plat-name=win32
python setup.py bdist_wininst --target-version=3.3 --plat-name=win32
python setup.py bdist_wininst --target-version=3.4 --plat-name=win32
python setup.py bdist_wininst --target-version=3.5 --plat-name=win32
