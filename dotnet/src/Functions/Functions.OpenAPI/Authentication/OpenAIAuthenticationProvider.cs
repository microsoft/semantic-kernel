// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Functions.OpenAPI.OpenAI;

namespace Microsoft.SemanticKernel.Functions.OpenAPI.Authentication;

/// <summary>
/// Provides authentication for HTTP requests to OpenAI using OAuth or verification tokens.
/// </summary>
public class OpenAIAuthenticationProvider
{
    private readonly Dictionary<string, Dictionary<string, string>> _oAuthValues;
    private readonly Dictionary<string, string> _credentials;

    /// <summary>
    /// Creates an instance of the <see cref="OpenAIAuthenticationProvider"/> class.
    /// </summary>
    /// <param name="oAuthValues">A dictionary containing OAuth values for each authentication scheme.</param>
    /// <param name="credentials">A dictionary containing credentials for each authentication scheme.</param>
    public OpenAIAuthenticationProvider(Dictionary<string, Dictionary<string, string>>? oAuthValues = null, Dictionary<string, string>? credentials = null)
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
    /// <param name="cancellationToken">The cancellation token.</param>
    public async Task AuthenticateRequestAsync(HttpRequestMessage request, string pluginName, OpenAIAuthenticationConfig openAIAuthConfig, CancellationToken cancellationToken = default)
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
                { "scope", openAIAuthConfig.Scope ?? "" },
            };

            HttpContent? requestContent = null;
            switch (openAIAuthConfig.AuthorizationContentType)
            {
                case OpenAIAuthorizationContentType.FormUrlEncoded:
                    requestContent = new FormUrlEncodedContent(values);
                    break;
                case OpenAIAuthorizationContentType.JSON:
                    requestContent = new StringContent(JsonSerializer.Serialize(values), Encoding.UTF8, OpenAIAuthorizationContentType.JSON.ToString());
                    break;
                default:
                    throw new SKException("Unsupported authorization content type.");
            }

            // Request the token
            using var client = new HttpClient();
            using var authRequest = new HttpRequestMessage(HttpMethod.Post, openAIAuthConfig.AuthorizationUrl) { Content = requestContent };
            var response = await client.SendWithSuccessCheckAsync(authRequest, cancellationToken).ConfigureAwait(false);
            requestContent.Dispose();

            if (!response.IsSuccessStatusCode)
            {
                throw new SKException($"Failed to get token from {openAIAuthConfig.AuthorizationUrl}.");
            }

            // Read the token
            var responseContent = await response.Content.ReadAsStringWithExceptionMappingAsync().ConfigureAwait(false);
            OAuthTokenResponse? tokenResponse;
            try
            {
                tokenResponse = JsonSerializer.Deserialize<OAuthTokenResponse>(responseContent);
            }
            catch (JsonException)
            {
                throw new SKException($"Failed to deserialize token response from {openAIAuthConfig.AuthorizationUrl}.");
            }

            // Get the token type and value
            scheme = tokenResponse?.TokenType ?? throw new SKException("No token type found in the response.");
            credential = tokenResponse?.AccessToken ?? throw new SKException("No access token found in the response.");
        }
        else
        {
            var token = openAIAuthConfig.VerificationTokens?[pluginName]
                ?? throw new SKException("No verification token found for the provided plugin name.");

            scheme = openAIAuthConfig.AuthorizationType.ToString();
            credential = token;
        }

        request.Headers.Authorization = new AuthenticationHeaderValue(scheme, credential);
    }
}
