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

    private readonly ILogger<ApiKeyAuthenticationHandler> _logger;

    /// <summary>
    /// Constructor
    /// </summary>
    public ApiKeyAuthenticationHandler(
        IOptionsMonitor<ApiKeyAuthenticationSchemeOptions> options,
        ILoggerFactory logger,
        UrlEncoder encoder,
        ISystemClock clock) : base(options, logger, encoder, clock)
    {
        this._logger = logger.CreateLogger<ApiKeyAuthenticationHandler>();
    }

    protected override Task<AuthenticateResult> HandleAuthenticateAsync()
    {
        this._logger.LogInformation("Checking API key");

        if (string.IsNullOrWhiteSpace(this.Options.ApiKey))
        {
            const string ErrorMessage = "API key not configured on server";

            this._logger.LogError(ErrorMessage);

            return Task.FromResult(AuthenticateResult.Fail(ErrorMessage));
        }

        if (!this.Request.Headers.TryGetValue(ApiKeyHeaderName, out StringValues apiKeyFromHeader))
        {
            const string InformationMessage = "No API key provided";

            this._logger.LogWarning(InformationMessage);

            return Task.FromResult(AuthenticateResult.Fail(InformationMessage));
        }

        if (!string.Equals(apiKeyFromHeader, this.Options.ApiKey, StringComparison.Ordinal))
        {
            const string WarningMessage = "Incorrect API key";

            this._logger.LogWarning(WarningMessage);

            return Task.FromResult(AuthenticateResult.Fail(WarningMessage));
        }

        var principal = new ClaimsPrincipal(new ClaimsIdentity(AuthenticationScheme));
        var ticket = new AuthenticationTicket(principal, this.Scheme.Name);

        this._logger.LogInformation("Request authorized by API key");

        return Task.FromResult(AuthenticateResult.Success(ticket));
    }
}
