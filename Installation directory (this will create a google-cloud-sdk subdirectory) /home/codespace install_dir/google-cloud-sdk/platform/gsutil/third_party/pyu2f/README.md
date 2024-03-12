# pyu2f

[![Build Status](https://travis-ci.org/google/pyu2f.svg?branch=master)](https://travis-ci.org/google/pyu2f)

pyu2f is a python based U2F host library for Linux, Windows, and MacOS. It
provides functionality for interacting with a U2F device over USB.

## Features

pyu2f uses ctypes to make system calls directly to interface with the USB HID
device. This means that no platform specific shared libraries need to be
compiled for pyu2f to work.

By default pyu2f will use its own U2F stack implementation to sign requests. If
desired, pyu2f can offload signing to a pluggable command line tool. Offloading
is not yet supported for U2F registration.

## Usage

The recommended approach for U2F signing (authentication) is through the
convenience interface:

```
from pyu2f import model
from pyu2f.convenience import authenticator

...

registered_key = model.RegisteredKey(b64_encoded_key)
challenge_data = [{'key': registered_key, 'challenge': raw_challenge_data}]

api = authenticator.CreateCompositeAuthenticator(origin)
response = api.Authenticate(app_id, challenge_data)

```

See baseauthenticator.py for interface details.

## Authentication Plugin

The convenience interface allows for a pluggable authenticator to be defined and
used instead of the built in U2F stack.

This can be done by setting the SK_SIGNING_PLUGIN environment variable to the
plugin tool. The plugin tool should follow the specification detailed in
customauthenticator.py

If SK_SIGNING_PLUGIN is set, the convenience layer will invoke the signing
plugin whenver Authenticate() is called.
