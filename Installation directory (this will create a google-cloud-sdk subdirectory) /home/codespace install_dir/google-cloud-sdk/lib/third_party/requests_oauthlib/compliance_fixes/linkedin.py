from json import loads, dumps

from oauthlib.common import add_params_to_uri, to_unicode


def linkedin_compliance_fix(session):

  def _missing_token_type(r):
    token = loads(r.text)
    token['token_type'] = 'Bearer'
    r._content = to_unicode(dumps(token)).encode('UTF-8')
    return r

  def _non_compliant_param_name(url, headers, data):
    token = [('oauth2_access_token', session.access_token)]
    url = add_params_to_uri(url, token)
    return url, headers, data

  session._client.default_token_placement = 'query'
  session.register_compliance_hook('access_token_response', _missing_token_type)
  session.register_compliance_hook('protected_request',
                                   _non_compliant_param_name)
  return session
