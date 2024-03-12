# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Helpers for building x509 parameters using a preset profile."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.util import messages as messages_util
from googlecloudsdk.calliope import exceptions

_LEAF_CLIENT_TLS = {
    'caOptions': {
        'isCa': False
    },
    'keyUsage': {
        'extendedKeyUsage': {
            'clientAuth': True
        },
        'baseKeyUsage': {
            'digitalSignature': True,
            'keyEncipherment': True
        }
    }
}

_LEAF_CODE_SIGNING = {
    'caOptions': {
        'isCa': False
    },
    'keyUsage': {
        'extendedKeyUsage': {
            'codeSigning': True
        },
        'baseKeyUsage': {
            'digitalSignature': True,
            'contentCommitment': True
        }
    }
}

_LEAF_MTLS = {
    'caOptions': {
        'isCa': False
    },
    'keyUsage': {
        'extendedKeyUsage': {
            'serverAuth': True,
            'clientAuth': True
        },
        'baseKeyUsage': {
            'digitalSignature': True,
            'keyEncipherment': True
        }
    }
}

_LEAF_SERVER_TLS = {
    'caOptions': {
        'isCa': False
    },
    'keyUsage': {
        'extendedKeyUsage': {
            'serverAuth': True
        },
        'baseKeyUsage': {
            'digitalSignature': True,
            'keyEncipherment': True
        }
    }
}

_LEAF_SMIME = {
    'caOptions': {
        'isCa': False
    },
    'keyUsage': {
        'extendedKeyUsage': {
            'emailProtection': True
        },
        'baseKeyUsage': {
            'digitalSignature': True,
            'contentCommitment': True
        }
    }
}

_ROOT_UNCONSTRAINED = {
    'caOptions': {
        'isCa': True
    },
    'keyUsage': {
        'baseKeyUsage': {
            'certSign': True,
            'crlSign': True
        }
    }
}

_SUBORDINATE_CLIENT_TLS_PATHLEN_0 = {
    'caOptions': {
        'isCa': True,
        'maxIssuerPathLength': 0
    },
    'keyUsage': {
        'extendedKeyUsage': {
            'clientAuth': True
        },
        'baseKeyUsage': {
            'certSign': True,
            'crlSign': True
        }
    }
}

_SUBORDINATE_CODE_SIGNING_PATHLEN_0 = {
    'caOptions': {
        'isCa': True,
        'maxIssuerPathLength': 0
    },
    'keyUsage': {
        'extendedKeyUsage': {
            'codeSigning': True
        },
        'baseKeyUsage': {
            'certSign': True,
            'crlSign': True
        }
    }
}

_SUBORDINATE_MTLS_PATHLEN_0 = {
    'caOptions': {
        'isCa': True,
        'maxIssuerPathLength': 0
    },
    'keyUsage': {
        'extendedKeyUsage': {
            'serverAuth': True,
            'clientAuth': True
        },
        'baseKeyUsage': {
            'certSign': True,
            'crlSign': True
        }
    }
}

_SUBORDINATE_SERVER_TLS_PATHLEN_0 = {
    'caOptions': {
        'isCa': True,
        'maxIssuerPathLength': 0
    },
    'keyUsage': {
        'extendedKeyUsage': {
            'serverAuth': True
        },
        'baseKeyUsage': {
            'certSign': True,
            'crlSign': True
        }
    }
}

_SUBORDINATE_SMIME_PATHLEN_0 = {
    'caOptions': {
        'isCa': True,
        'maxIssuerPathLength': 0
    },
    'keyUsage': {
        'extendedKeyUsage': {
            'emailProtection': True
        },
        'baseKeyUsage': {
            'certSign': True,
            'crlSign': True
        }
    }
}

_SUBORDINATE_UNCONSTRAINED_PATHLEN_0 = {
    'caOptions': {
        'isCa': True,
        'maxIssuerPathLength': 0
    },
    'keyUsage': {
        'baseKeyUsage': {
            'certSign': True,
            'crlSign': True
        }
    }
}

_PRESET_PROFILES = {
    'leaf_client_tls': _LEAF_CLIENT_TLS,
    'leaf_code_signing': _LEAF_CODE_SIGNING,
    'leaf_mtls': _LEAF_MTLS,
    'leaf_server_tls': _LEAF_SERVER_TLS,
    'leaf_smime': _LEAF_SMIME,
    'root_unconstrained': _ROOT_UNCONSTRAINED,
    'subordinate_client_tls_pathlen_0': _SUBORDINATE_CLIENT_TLS_PATHLEN_0,
    'subordinate_code_signing_pathlen_0': _SUBORDINATE_CODE_SIGNING_PATHLEN_0,
    'subordinate_mtls_pathlen_0': _SUBORDINATE_MTLS_PATHLEN_0,
    'subordinate_server_tls_pathlen_0': _SUBORDINATE_SERVER_TLS_PATHLEN_0,
    'subordinate_smime_pathlen_0': _SUBORDINATE_SMIME_PATHLEN_0,
    'subordinate_unconstrained_pathlen_0': _SUBORDINATE_UNCONSTRAINED_PATHLEN_0
}


def GetPresetProfileOptions():
  """Returns the possible string options for the use-preset-profile flag."""
  return sorted(_PRESET_PROFILES.keys())


def GetPresetX509Parameters(profile_name):
  """Parses the profile name string into the corresponding API X509Parameters.

  Args:
    profile_name: The preset profile name.

  Returns:
    An X509Parameters object.
  """
  if profile_name not in _PRESET_PROFILES:
    raise exceptions.InvalidArgumentException(
        '--use-preset-profile',
        'The preset profile that was specified does not exist.')
  messages = privateca_base.GetMessagesModule('v1')
  return messages_util.DictToMessageWithErrorCheck(
      _PRESET_PROFILES[profile_name], messages.X509Parameters)
