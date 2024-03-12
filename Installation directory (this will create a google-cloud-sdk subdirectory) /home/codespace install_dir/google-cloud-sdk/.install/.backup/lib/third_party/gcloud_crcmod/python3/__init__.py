try:
    from gcloud_crcmod.python3.crcmod import *
    import gcloud_crcmod.python3.predefined
except ImportError:
    # Make this backward compatible
    from crcmod import *
    import predefined
__doc__ = crcmod.__doc__
