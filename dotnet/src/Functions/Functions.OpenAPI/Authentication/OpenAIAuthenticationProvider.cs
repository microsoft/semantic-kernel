// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Functions.OpenAPI.Authentication;

/// <summary>
/// An example of OpenAI auth provider.
/// </summary>
public class OpenAIAuthenticationProvider
{
    private readonly OpenAIAuthenticationManifest _manifest;

    /// <summary>
    /// Creates an instance of the <see cref="BearerAuthenticationProvider"/> class.
    /// </summary>
    /// <param name="manifest">OpenAI auth manifest</param>
    public OpenAIAuthenticationProvider(OpenAIAuthenticationManifest manifest)
    {
        this._manifest = manifest;
    }

    /// <summary>
    /// Applies the token to the provided HTTP request message.
    /// </summary>
    /// <param name="request">The HTTP request message.</param>
    public async Task AuthenticateRequestAsync(HttpRequestMessage request)
    {
        var token = "fake-token"; //Implement all the required logic to parse the manifest and issue an auth token according to the manifest.
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
    }
}
