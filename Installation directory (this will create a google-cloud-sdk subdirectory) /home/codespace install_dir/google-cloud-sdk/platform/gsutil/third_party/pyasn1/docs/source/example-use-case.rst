
Example use case
================

.. toctree::
   :maxdepth: 2

To briefly explain how to approach pyasn1, consider a quick workflow example.

Grab ASN.1 schema for SSH keys
------------------------------

ASN.1 is widely used in many Internet protocols. Frequently, whenever ASN.1 is employed,
data structures are described in ASN.1 schema language right in the RFC.
Take `RFC2437 <https://www.ietf.org/rfc/rfc2437.txt>`_ for example -- we can look into
it and weed out data structures specification into a local file:

.. code-block:: python

    # pkcs-1.asn

    PKCS-1 {iso(1) member(2) us(840) rsadsi(113549) pkcs(1) pkcs-1(1) modules(0) pkcs-1(1)}

    DEFINITIONS EXPLICIT TAGS ::= BEGIN
        RSAPrivateKey ::= SEQUENCE {
             version Version,
             modulus INTEGER,
             publicExponent INTEGER,
             privateExponent INTEGER,
             prime1 INTEGER,
             prime2 INTEGER,
             exponent1 INTEGER,
             exponent2 INTEGER,
             coefficient INTEGER
        }
        Version ::= INTEGER
    END

Compile ASN.1 schema into Python
--------------------------------

In the best case, you should be able to automatically compile ASN.1 spec into
Python classes. For that purpose we have the `asn1ate <https://github.com/kimgr/asn1ate>`_
tool:

.. code-block:: bash

    $ pyasn1gen.py pkcs-1.asn > rsakey.py

Though it may not work out as, as it stands now, asn1ate does not support
all ASN.1 language constructs.

Alternatively, you could check out the `pyasn1-modules <https://github.com/etingof/pyasn1-modules>`_
package to see if it already has the ASN.1 spec you are looking for compiled and shipped
there. Then just install the package, import the data structure you need and use it:

.. code-block:: bash

    $ pip install pyasn1-modules

As a last resort, you could express ASN.1 in Python by hand. The end result
should be a declarative Python code resembling original ASN.1 syntax like
this:

.. code-block:: python

    # rsakey.py

    class Version(Integer):
        pass

    class RSAPrivateKey(Sequence):
        componentType = NamedTypes(
            NamedType('version', Version()),
            NamedType('modulus', Integer()),
            NamedType('publicExponent', Integer()),
            NamedType('privateExponent', Integer()),
            NamedType('prime1', Integer()),
            NamedType('prime2', Integer()),
            NamedType('exponent1', Integer()),
            NamedType('exponent2', Integer()),
            NamedType('coefficient', Integer())
        )

Read your ~/.ssh/id_rsa
-----------------------

Given we've put our Python classes into the `rsakey.py` module, we could import
the top-level object for SSH keys container and initialize it from our
`~/.ssh/id_rsa` file (for sake of simplicity here we assume no passphrase is
set on the key file):

.. code-block:: python

    from base64 import b64decode
    from pyasn1.codec.der.decoder import decode as der_decoder
    from rsakey import RSAPrivateKey

    # Read SSH key from file (assuming no passphrase)
    with open open('.ssh/id_rsa') as key_file:
        b64_serialisation = ''.join(key_file.readlines()[1:-1])

    # Undo BASE64 serialisation
    der_serialisation = b64decode(b64_serialisation)

    # Undo DER serialisation, reconstruct SSH key structure
    private_key, rest_of_input = der_decoder(der_serialisation, asn1Spec=RSAPrivateKey())

Once we have Python ASN.1 structures initialized, we could inspect them:

.. code-block:: pycon

    >>> print('%s' % private_key)
    RSAPrivateKey:
     version=0
     modulus=280789907761334970323210643584308373...
     publicExponent=65537
     privateExponent=1704567874679144879123080924...
     prime1=1780178536719561265324798296279384073...
     prime2=1577313184995269616049017780493740138...
     exponent1=1193974819720845247396384239609024...
     exponent2=9240965721817961178848297404494811...
     coefficient=10207364473358910343346707141115...

Play with the keys
------------------

As well as use them nearly as we do with native Python types:

.. code-block:: pycon

    >>> pk = private_key
    >>>
    >>> pk['prime1'] * pk['prime2'] == pk['modulus']
    True
    >>> pk['prime1'] == pk['modulus'] // pk['prime2']
    True
    >>> pk['exponent1'] == pk['privateExponent'] % (pk['prime1'] - 1)
    True
    >>> pk['exponent2'] == pk['privateExponent'] % (pk['prime2'] - 1)
    True

Technically, pyasn1 classes `emulate <https://docs.python.org/3/reference/datamodel.html#emulating-container-types>`_
Python built-in types.

Transform to built-ins
----------------------

ASN.1 data structures exhibit a way more complicated behaviour compared to
Python types. You may wish to simplify things by turning the whole tree of
pyasn1 objects into an analogous tree made of base Python types:

.. code-block:: pycon

    >>> from pyasn1.codec.native.encoder import encode
    >>> ...
    >>> py_private_key = encode(private_key)
    >>> py_private_key
    {'version': 0, 'modulus': 280789907761334970323210643584308373, 'publicExponent': 65537,
     'privateExponent': 1704567874679144879123080924, 'prime1': 1780178536719561265324798296279384073,
     'prime2': 1577313184995269616049017780493740138, 'exponent1': 1193974819720845247396384239609024,
     'exponent2': 9240965721817961178848297404494811, 'coefficient': 10207364473358910343346707141115}

You can do vice-versa: initialize ASN.1 structure from a dict:

.. code-block:: pycon

    >>> from pyasn1.codec.native.decoder import decode
    >>> py_private_key = {'modulus': 280789907761334970323210643584308373}
    >>> private_key = decode(py_private_key, asn1Spec=RSAPrivateKey())

Write it back
-------------

Possibly not that applicable to the SSH key example, but you can of course modify
any part of the ASN.1 data structure and serialise it back into the same or other
wire representation:

.. code-block:: python

    from pyasn1.codec.der.encoder import encode as der_encoder

    # Serialise SSH key data structure into DER stream
    der_serialisation = der_encoder(private_key)

    # Serialise DER stream into BASE64 stream
    b64_serialisation = '-----BEGIN RSA PRIVATE KEY-----\n'
    b64_serialisation += b64encode(der_serialisation)
    b64_serialisation += '-----END RSA PRIVATE KEY-----\n'

    with open('.ssh/id_rsa.new', 'w') as key_file:
        key_file.write(b64_serialisation)

