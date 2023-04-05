// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Authentication;

public class TokenAuthenticationProvider
{
    private readonly string _accessToken;

    public TokenAuthenticationProvider(string accessToken)
    {
        this._accessToken = accessToken;
    }
    
    public Task AuthenticateRequestAsync(HttpRequestMessage request)
    {
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", this._accessToken);
        return Task.CompletedTask;
    }
}
