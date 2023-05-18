// Copyright (c) Microsoft. All rights reserved.

using System;
using Azure.Identity;
using Microsoft.AspNetCore.Http;
using Microsoft.IdentityModel.JsonWebTokens;

namespace SemanticKernel.Service.Auth;

/// <summary>
/// Class which provides validated security information for use in controllers.
/// </summary>
public class AuthInfo : IAuthInfo
{
    private readonly Lazy<string> _userId;

    public AuthInfo(IHttpContextAccessor httpContextAccessor)
    {
        _userId = new Lazy<string>(() =>
        {
            var user = httpContextAccessor.HttpContext?.User;
            if (user is null)
            {
                throw new InvalidOperationException("HttpContext must be present to inspect auth info.");
            }
            var userIdClaim = user.FindFirst("oid")
                ?? user.FindFirst(JwtRegisteredClaimNames.Sub);

            if (userIdClaim is null)
            {
                throw new CredentialUnavailableException("User Id was not present in the request token.");
            }
            return userIdClaim.Value;
        }, isThreadSafe: false);
    }

    /// <summary>
    /// The authenticated user's unique ID.
    /// </summary>
    public string UserId => _userId.Value;
}
