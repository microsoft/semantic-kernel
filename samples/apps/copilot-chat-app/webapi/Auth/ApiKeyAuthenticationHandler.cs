// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Security.Claims;
using System.Text.Encodings.Web;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Authentication;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Microsoft.Extensions.Primitives;

namespace SemanticKernel.Service.Auth;

/// <summary>
/// Class implementing API key authentication.
/// </summary>
public class ApiKeyAuthenticationHandler : AuthenticationHandler<ApiKeyAuthenticationSchemeOptions>
{
    public const string AuthenticationScheme = "ApiKey";
    public const string ApiKeyHeaderName = "x-sk-api-key";

    /// <summary>
    /// Constructor
    /// </summary>
    public ApiKeyAuthenticationHandler(
        IOptionsMonitor<ApiKeyAuthenticationSchemeOptions> options,
        ILoggerFactory loggerFactory,
        UrlEncoder encoder,
        ISystemClock clock) : base(options, loggerFactory, encoder, clock)
    {
    }

    protected override Task<AuthenticateResult> HandleAuthenticateAsync()
    {
        this.Logger.LogInformation("Checking API key");

        if (string.IsNullOrWhiteSpace(this.Options.ApiKey))
        {
            const string ErrorMessage = "API key not configured on server";

            this.Logger.LogError(ErrorMessage);

            return Task.FromResult(AuthenticateResult.Fail(ErrorMessage));
        }

        if (!this.Request.Headers.TryGetValue(ApiKeyHeaderName, out StringValues apiKeyFromHeader))
        {
            const string WarningMessage = "No API key provided";

            this.Logger.LogWarning(WarningMessage);

            return Task.FromResult(AuthenticateResult.Fail(WarningMessage));
        }

        if (!string.Equals(apiKeyFromHeader, this.Options.ApiKey, StringComparison.Ordinal))
        {
            const string WarningMessage = "Incorrect API key";

            this.Logger.LogWarning(WarningMessage);

            return Task.FromResult(AuthenticateResult.Fail(WarningMessage));
        }

        var principal = new ClaimsPrincipal(new ClaimsIdentity(AuthenticationScheme));
        var ticket = new AuthenticationTicket(principal, this.Scheme.Name);

        this.Logger.LogInformation("Request authorized by API key");

        return Task.FromResult(AuthenticateResult.Success(ticket));
    }
}
