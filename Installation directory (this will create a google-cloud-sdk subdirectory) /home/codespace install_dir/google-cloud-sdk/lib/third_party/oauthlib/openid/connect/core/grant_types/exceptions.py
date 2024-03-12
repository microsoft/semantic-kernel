class OIDCNoPrompt(Exception):
  """Exception used to inform users that no explicit authorization is needed.

    Normally users authorize requests after validation of the request is done.
    Then post-authorization validation is again made and a response containing
    an auth code or token is created. However, when OIDC clients request
    no prompting of user authorization the final response is created directly.

    Example (without the shortcut for no prompt)

    scopes, req_info = endpoint.validate_authorization_request(url, ...)
    authorization_view = create_fancy_auth_form(scopes, req_info)
    return authorization_view

    Example (with the no prompt shortcut)
    try:
        scopes, req_info = endpoint.validate_authorization_request(url, ...)
        authorization_view = create_fancy_auth_form(scopes, req_info)
        return authorization_view
    except OIDCNoPrompt:
        # Note: Location will be set for you
        headers, body, status = endpoint.create_authorization_response(url, ...)
        redirect_view = create_redirect(headers, body, status)
        return redirect_view
    """

  def __init__(self):
    msg = ("OIDC request for no user interaction received. Do not ask user "
           "for authorization, it should been done using silent "
           "authentication through create_authorization_response. "
           "See OIDCNoPrompt.__doc__ for more details.")
    super(OIDCNoPrompt, self).__init__(msg)
