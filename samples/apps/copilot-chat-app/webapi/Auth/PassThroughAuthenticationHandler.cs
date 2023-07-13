// Copyright (c) Microsoft. All rights reserved.

using System.Security.Claims;
using System.Text.Encodings.Web;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Authentication;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace SemanticKernel.Service.Auth;

/// <summary>
/// Class implementing "authentication" that lets all requests pass through.
/// </summary>
public class PassThroughAuthenticationHandler : AuthenticationHandler<AuthenticationSchemeOptions>
{
    public const string AuthenticationScheme = "PassThrough";

    /// <summary>
    /// Constructor
    /// </summary>
    public PassThroughAuthenticationHandler(
        IOptionsMonitor<AuthenticationSchemeOptions> options,
        ILoggerFactory loggerFactory,
        UrlEncoder encoder,
        ISystemClock clock) : base(options, loggerFactory, encoder, clock)
    {
    }

    protected override Task<AuthenticateResult> HandleAuthenticateAsync()
    {
        this.Logger.LogInformation("Allowing request to pass through");

        var principal = new ClaimsPrincipal(new ClaimsIdentity(AuthenticationScheme));
        var ticket = new AuthenticationTicket(principal, this.Scheme.Name);

        return Task.FromResult(AuthenticateResult.Success(ticket));
    }
}
