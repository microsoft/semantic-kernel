#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
import argcomplete, argparse, requests, pprint

def github_org_members(prefix, parsed_args, **kwargs):
    resource = "https://api.github.com/orgs/{org}/members".format(org=parsed_args.organization)
    return (member['login'] for member in requests.get(resource).json() if member['login'].startswith(prefix))

parser = argparse.ArgumentParser()
parser.add_argument("--organization", help="GitHub organization")
parser.add_argument("--member", help="GitHub member").completer = github_org_members

argcomplete.autocomplete(parser)
args = parser.parse_args()

pprint.pprint(requests.get("https://api.github.com/users/{m}".format(m=args.member)).json())
