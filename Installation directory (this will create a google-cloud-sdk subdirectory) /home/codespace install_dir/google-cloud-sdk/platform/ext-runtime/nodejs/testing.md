
Testing Notes
=============

To run the test script (`test/runtime_test.py`) you'll need to install the
Google Cloud SDK add this to your PYTHONPATH:

    export PYTHONPATH=$CLOUD_SDK/lib:$CLOUD_SDK/platform/google_appengine:$PYTHONPATH

Where `$CLOUD_SDK` is the location where the cloud SDK is installed.

Debugging
---------

If you do "sys.stderr.write(...)" from a plugin script, your output will go
to a nice shiny bright warning message.  Exceptions will show up as warning
messages simply by virtue of having been formatted to standard error.

Full logging can be made to happen by adding:

    from googlecloudsdk.core import log
    log.SetVerbosity(logging.DEBUG)
