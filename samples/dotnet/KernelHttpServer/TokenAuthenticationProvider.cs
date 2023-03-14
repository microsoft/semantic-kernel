// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading.Tasks;
using Microsoft.Graph;

namespace KernelHttpServer;

internal sealed class TokenAuthenticationProvider : IAuthenticationProvider
{
    private readonly string _token;

    public TokenAuthenticationProvider(string token)
    {
        this._token = token;
    }

    public Task AuthenticateRequestAsync(HttpRequestMessage request)
    {
        return Task.FromResult(request.Headers.Authorization = new AuthenticationHeaderValue(
            scheme: "bearer",
            parameter: this._token));
    }
}
