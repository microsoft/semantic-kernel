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

public class DynamicAuthenticationProvider
{
    private readonly Dictionary<string, Dictionary<string, string>> _oAuthValues;
    private readonly Dictionary<string, string> _credentials;

    public DynamicAuthenticationProvider(Dictionary<string, Dictionary<string, string>> oAuthValues, Dictionary<string, string> credentials)
    {
        this._oAuthValues = oAuthValues;
        this._credentials = credentials;
    }

    /// <summary>
    /// Applies the authentication content to the provided HTTP request message.
    /// </summary>
    /// <param name="request">The HTTP request message.</param>
    /// <param name="authConfig">The <see cref="OpenAIAuthenticationManifest"/> used to authenticate.</param>
    public async Task AuthenticateRequestAsync(HttpRequestMessage request, OpenAIAuthenticationManifest? authConfig = null)
    {
        if (authConfig == null || authConfig.Type == OpenAIAuthenticationType.None)
        {
            return;
        }

        string scheme = "";
        string credential = "";

        if (authConfig.Type == OpenAIAuthenticationType.OAuth)
        {
            var domainOAuthValues = this._oAuthValues[authConfig.ClientUrl!.Host];
            if (domainOAuthValues == null)
            {
                throw new SKException("No OAuth values found for the provided client URL.");
            }

            var values = new Dictionary<string, string>(domainOAuthValues) {
                { "scope", authConfig.Scope ?? "" },
            };

            HttpContent? content = null;
            switch (authConfig.AuthorizationContentType)
            {
                case OpenAIAuthorizationContentType.FormUrlEncoded:
                    content = new FormUrlEncodedContent(values);
                    break;
                case OpenAIAuthorizationContentType.JSON:
                    content = new StringContent(JsonSerializer.Serialize(values), Encoding.UTF8, authConfig.AuthorizationContentType.ToString());
                    break;
                default:
                    // Handle other cases as needed
                    break;
            }

            // Request the token
            using var client = new HttpClient();
            var response = await client.PostAsync(authConfig.AuthorizationUrl, content).ConfigureAwait(false);

            if (response.IsSuccessStatusCode)
            {
                // Read the token
                var tokenResponse = JsonNode.Parse(await response.Content.ReadAsStringAsync().ConfigureAwait(false))!;

                // Get the type and token value
                scheme = tokenResponse["token_type"]!.ToString();
                credential = tokenResponse["access_token"]!.ToString();
            }

            content?.Dispose();
        }
        else
        {
            scheme = authConfig.AuthorizationType.ToString();

            // PROBLEM: the user will have different credentials for different pluginS, but at this point we do not know 
            // which plugin we are loading... need a way to know the host or name for the plugin being loaded so that the correct
            // credential can be pulled from the dictionary
            // POSSIBLE SOLUTION: use the OpenAI verification token to determine the unique identity of the plugin?
            credential = this._credentials[authConfig.VerificationTokens!["openai"]];
        }

        request.Headers.Authorization = new AuthenticationHeaderValue(scheme, credential);
    }
}
