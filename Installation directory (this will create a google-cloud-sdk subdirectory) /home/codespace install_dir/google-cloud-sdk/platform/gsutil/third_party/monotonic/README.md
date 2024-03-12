monotonic
=========
This module provides a ``monotonic()`` function which returns the
value (in fractional seconds) of a clock which never goes backwards.
It is compatible with Python 2 and Python 3.

On Python 3.3 or newer, ``monotonic`` will be an alias of
[``time.monotonic``][0] from the standard library. On older versions,
it will fall back to an equivalent implementation:

 OS              | Implementation
-----------------|-----------------------------------------
 Linux, BSD, AIX | [clock_gettime][1]
 Windows         | [GetTickCount][2] or [GetTickCount64][3]
 OS X            | [mach_absolute_time][3]

If no suitable implementation exists for the current platform,
attempting to import this module (or to import from it) will
cause a RuntimeError exception to be raised.

monotonic is available via the Python Cheese Shop (PyPI):
  https://pypi.python.org/pypi/monotonic/

License
-------
Copyright 2014, 2015, 2016, 2017 Ori Livneh <ori@wikimedia.org>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

[0]: https://docs.python.org/3/library/time.html#time.monotonic
[1]: http://linux.die.net/man/3/clock_gettime
[2]: https://msdn.microsoft.com/en-us/library/windows/desktop/ms724408
[3]: https://msdn.microsoft.com/en-us/library/windows/desktop/ms724411
[4]: https://developer.apple.com/library/mac/qa/qa1398/
