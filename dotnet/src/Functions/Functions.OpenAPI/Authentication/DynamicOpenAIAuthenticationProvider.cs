// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Functions.OpenAPI.Authentication;

/// <summary>
/// Provides dynamic authentication for HTTP requests to OpenAI using OAuth or verification tokens.
/// </summary>
public class DynamicOpenAIAuthenticationProvider
{
    private readonly Dictionary<string, Dictionary<string, string>> _oAuthValues;
    private readonly Dictionary<string, string> _credentials;

    /// <summary>
    /// Creates an instance of the <see cref="DynamicOpenAIAuthenticationProvider"/> class.
    /// </summary>
    /// <param name="oAuthValues">A dictionary containing OAuth values for each authentication scheme.</param>
    /// <param name="credentials">A dictionary containing credentials for each authentication scheme.</param>
    public DynamicOpenAIAuthenticationProvider(Dictionary<string, Dictionary<string, string>>? oAuthValues = null, Dictionary<string, string>? credentials = null)
    {
        this._oAuthValues = oAuthValues ?? new();
        this._credentials = credentials ?? new();
    }

    /// <summary>
    /// Applies the authentication content to the provided HTTP request message.
    /// </summary>
    /// <param name="request">The HTTP request message.</param>
    /// <param name="pluginName">Name of the plugin</param>
    /// <param name="openAIAuthConfig ">The <see cref="OpenAIAuthenticationConfig"/> used to authenticate.</param>
    public async Task AuthenticateRequestAsync(HttpRequestMessage request, string pluginName, OpenAIAuthenticationConfig openAIAuthConfig)
    {
        if (openAIAuthConfig.Type == OpenAIAuthenticationType.None)
        {
            return;
        }

        string scheme = "";
        string credential = "";

        if (openAIAuthConfig.Type == OpenAIAuthenticationType.OAuth)
        {
            var domainOAuthValues = this._oAuthValues[openAIAuthConfig.AuthorizationUrl!.Host]
                ?? throw new SKException("No OAuth values found for the provided authorization URL.");

            var values = new Dictionary<string, string>(domainOAuthValues) {
                { "scope", openAIAuthConfig .Scope ?? "" },
            };

            HttpContent? content = null;
            switch (openAIAuthConfig.AuthorizationContentType)
            {
                case OpenAIAuthorizationContentType.FormUrlEncoded:
                    content = new FormUrlEncodedContent(values);
                    break;
                case OpenAIAuthorizationContentType.JSON:
                    content = new StringContent(JsonSerializer.Serialize(values), Encoding.UTF8, openAIAuthConfig.AuthorizationContentType.ToString());
                    break;
                default:
                    // Handle other cases as needed
                    break;
            }

            // Request the token
            using var client = new HttpClient();
            var response = await client.PostAsync(openAIAuthConfig.AuthorizationUrl, content).ConfigureAwait(false);
            content?.Dispose();

            if (response.IsSuccessStatusCode)
            {
                // Read the token
                var tokenResponse = JsonNode.Parse(await response.Content.ReadAsStringAsync().ConfigureAwait(false))!;

                // Get the token type and value
                scheme = tokenResponse["token_type"]?.ToString()
                    ?? throw new SKException("No token type found in the response.");
                credential = tokenResponse["access_token"]?.ToString()
                    ?? throw new SKException("No access token found in the response.");
            }
        }
        else
        {
            var token = (openAIAuthConfig.VerificationTokens?[pluginName])
                ?? throw new SKException("No verification token found for the provided plugin name.");

            scheme = openAIAuthConfig.AuthorizationType.ToString();
            credential = token;
        }

        request.Headers.Authorization = new AuthenticationHeaderValue(scheme, credential);
    }
}
