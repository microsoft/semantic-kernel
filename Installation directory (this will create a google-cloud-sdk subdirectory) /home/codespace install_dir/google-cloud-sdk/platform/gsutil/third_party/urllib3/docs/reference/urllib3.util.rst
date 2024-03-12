Utilities
=========

Useful methods for working with :mod:`http.client`, completely decoupled from
code specific to **urllib3**.

At the very core, just like its predecessors, :mod:`urllib3` is built on top of
:mod:`http.client` -- the lowest level HTTP library included in the Python
standard library.

To aid the limited functionality of the :mod:`http.client` module, :mod:`urllib3`
provides various helper methods which are used with the higher level components
but can also be used independently.

.. automodule:: urllib3.util
    :members:
    :show-inheritance:
