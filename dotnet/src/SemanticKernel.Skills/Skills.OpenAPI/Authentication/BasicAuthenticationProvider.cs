// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Authentication;

/// <summary>
/// Retrieves authentication content (e.g. username/password, API key) via the provided delegate and
/// applies it to HTTP requests using the "basic" authentication scheme.
/// </summary>
public class BasicAuthenticationProvider
{
    private readonly Func<Task<string>> _content;

    /// <summary>
    /// Creates an instance of the <see cref="BasicAuthenticationProvider"/> class.
    /// </summary>
    /// <param name="content">Delegate for retrieving the authentication content.</param>
    public BasicAuthenticationProvider(Func<Task<string>> content)
    {
        this._content = content;
    }

    /// <summary>
    /// Applies the authentication content to the provided HTTP request message.
    /// </summary>
    /// <param name="request">The HTTP request message.</param>
    /// <returns></returns>
    public async Task AuthenticateRequestAsync(HttpRequestMessage request)
    {
        // Base64 encode
        string encodedContent = Convert.ToBase64String(Encoding.UTF8.GetBytes(await this._content()));
        request.Headers.Authorization = new AuthenticationHeaderValue("Basic", encodedContent);
    }
}
