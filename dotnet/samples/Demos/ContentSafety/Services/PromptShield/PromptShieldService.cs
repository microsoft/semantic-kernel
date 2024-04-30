// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Azure.AI.ContentSafety;
using Azure.Core;
using ContentSafety.Options;

namespace ContentSafety.Services.PromptShield;

/// <summary>
/// Performs request to Prompt Shield service for attack detection.
/// More information here: https://learn.microsoft.com/en-us/azure/ai-services/content-safety/quickstart-jailbreak#analyze-attacks
/// </summary>
public class PromptShieldService(
    ContentSafetyClient contentSafetyClient,
    AzureContentSafetyOptions azureContentSafetyOptions,
    string apiVersion = "2024-02-15-preview")
{
    private readonly ContentSafetyClient _contentSafetyClient = contentSafetyClient;
    private readonly AzureContentSafetyOptions _azureContentSafetyOptions = azureContentSafetyOptions;
    private readonly string _apiVersion = apiVersion;

    private Uri PromptShieldEndpoint
        => new($"{this._azureContentSafetyOptions.Endpoint}contentsafety/text:shieldPrompt?api-version={this._apiVersion}");

    public async Task<PromptShieldResponse> DetectAttackAsync(PromptShieldRequest request)
    {
        var httpRequest = this.CreateHttpRequest(request);
        var httpResponse = await this._contentSafetyClient.Pipeline.SendRequestAsync(httpRequest, default);

        var httpResponseContent = httpResponse.Content.ToString();

        return JsonSerializer.Deserialize<PromptShieldResponse>(httpResponseContent) ??
            throw new Exception("Invalid Prompt Shield response");
    }

    #region private

    private Request CreateHttpRequest(PromptShieldRequest request)
    {
        var httpRequest = this._contentSafetyClient.Pipeline.CreateRequest();

        var uri = new RequestUriBuilder();

        uri.Reset(this.PromptShieldEndpoint);

        httpRequest.Uri = uri;
        httpRequest.Method = RequestMethod.Post;
        httpRequest.Headers.Add("Accept", "application/json");
        httpRequest.Headers.Add("Content-Type", "application/json");
        httpRequest.Content = RequestContent.Create(JsonSerializer.Serialize(request));

        return httpRequest;
    }

    #endregion
}
