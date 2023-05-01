// Copyright (c) Microsoft. All rights reserved.

using System.Security.Claims;
using System.Text.Encodings.Web;
using Microsoft.AspNetCore.Authentication;
using Microsoft.Extensions.Options;
using Microsoft.Extensions.Primitives;

namespace SemanticKernel.Service.Auth;

/// <summary>
/// Class implementing API key authentication.
/// </summary>
public class ApiKeyAuthenticationHandler : AuthenticationHandler<ApiKeyAuthenticationSchemeOptions>
{
    public const string AuthenticationScheme = "ApiKey";
    public const string ApiKeyHeaderName = "x-api-key";

    // TODO: not used?
    private readonly IOptionsMonitor<ApiKeyAuthenticationSchemeOptions> _options;

    /// <summary>
    /// Constructor
    /// </summary>
    public ApiKeyAuthenticationHandler(
        IOptionsMonitor<ApiKeyAuthenticationSchemeOptions> options,
        ILoggerFactory logger,
        UrlEncoder encoder,
        ISystemClock clock) : base(options, logger, encoder, clock)
    {
        this._options = options;
    }

    protected override Task<AuthenticateResult> HandleAuthenticateAsync()
    {
        if (string.IsNullOrWhiteSpace(this.Options.ApiKey))
        {
            return Task.FromResult(AuthenticateResult.Fail("API key not configured on server"));
        }

        if (!this.Request.Headers.TryGetValue(ApiKeyHeaderName, out StringValues apiKeyFromHeader))
        {
            return Task.FromResult(AuthenticateResult.Fail("No API key provided"));
        }

        if (!string.Equals(apiKeyFromHeader, this.Options.ApiKey, StringComparison.Ordinal))
        {
            return Task.FromResult(AuthenticateResult.Fail("Incorrect API key"));
        }

        var principal = new ClaimsPrincipal(new ClaimsIdentity(AuthenticationScheme));
        var ticket = new AuthenticationTicket(principal, this.Scheme.Name);

        return Task.FromResult(AuthenticateResult.Success(ticket));
    }
}
