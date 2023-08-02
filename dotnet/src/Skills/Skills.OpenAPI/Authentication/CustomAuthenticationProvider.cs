// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Authentication;

/// <summary>
/// Retrieves authentication content (scheme and value) via the provided delegate and applies it to HTTP requests.
/// </summary>
public class CustomAuthenticationProvider
{
    private readonly Func<Task<string>> _header;
    private readonly Func<Task<string>> _value;

    /// <summary>
    /// Creates an instance of the <see cref="CustomAuthenticationProvider"/> class.
    /// </summary>
    /// <param name="header">Delegate for retrieving the header name.</param>
    /// <param name="value">Delegate for retrieving the value.</param>
    public CustomAuthenticationProvider(Func<Task<string>> header, Func<Task<string>> value)
    {
        this._header = header;
        this._value = value;
    }

    /// <summary>
    /// Applies the header and value to the provided HTTP request message.
    /// </summary>
    /// <param name="request">The HTTP request message.</param>
    /// <returns></returns>
    public async Task AuthenticateRequestAsync(HttpRequestMessage request)
    {
        var header = await this._header().ConfigureAwait(false);
        var value = await this._value().ConfigureAwait(false);
        request.Headers.Add(header, value);
    }
}
