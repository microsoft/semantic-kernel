// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Authentication;

/// <summary>
/// Stores an access token and uses it to authenticate HTTP requests.
/// This class implements the <see cref="AuthenticateRequestAsyncCallback"/> delegate.
/// </summary>
public class TokenAuthenticationProvider
{
    private readonly string _accessToken;

    /// <summary>
    /// Create an instance of the TokenAuthenticationProvider class with the given access token.
    /// </summary>
    /// <param name="accessToken">Access token.</param>
    public TokenAuthenticationProvider(string accessToken)
    {
        this._accessToken = accessToken;
    }

    /// <summary>
    /// Apply the token to the provided HTTP request message. The signature of this function matches
    /// the signature of the <see cref="AuthenticateRequestAsyncCallback"/> delegate.
    /// </summary>
    /// <param name="request">The HTTP request message.</param>
    /// <returns></returns>
    public Task AuthenticateRequestAsync(HttpRequestMessage request)
    {
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", this._accessToken);
        return Task.CompletedTask;
    }
}
