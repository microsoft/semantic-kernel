// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Authentication;

/// <summary>
/// Retrieves the title secret key via the provided delegate and
/// applies it to HTTP requests using the required authentication scheme.
/// </summary>
public class PlayFabAuthenticationProvider
{
    private readonly Func<Task<string>> _titleSecretKey;

    /// <summary>
    /// Creates an instance of the <see cref="PlayFabAuthenticationProvider"/> class.
    /// </summary>
    /// <param name="titleSecretKey">Delegate for retrieving the title secret key.</param>
    public PlayFabAuthenticationProvider(Func<Task<string>> titleSecretKey)
    {
        this._titleSecretKey = titleSecretKey;
    }

    /// <summary>
    /// Applies the authentication content to the provided HTTP request message.
    /// </summary>
    /// <param name="request">The HTTP request message.</param>
    public async Task AuthenticateRequestAsync(HttpRequestMessage request)
    {
        var titleSecretKey = await this._titleSecretKey().ConfigureAwait(false);
        request.Headers.Add("X-SecretKey", titleSecretKey);
    }
}
