// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Azure.AI.ContentSafety;
using Azure.Core;
using ContentSafety.Options;
using Microsoft.Extensions.Options;

namespace ContentSafety.Services.PromptShield;

public class PromptShieldService(
    ContentSafetyClient contentSafetyClient,
    IOptions<AzureContentSafetyOptions> azureContentSafetyOptions,
    string apiVersion = "2024-02-15-preview")
{
    private readonly ContentSafetyClient _contentSafetyClient = contentSafetyClient;
    private readonly AzureContentSafetyOptions _azureContentSafetyOptions = azureContentSafetyOptions.Value;
    private readonly string _apiVersion = apiVersion;

    private Uri PromptShieldEndpoint
        => new($"{this._azureContentSafetyOptions.Endpoint}contentsafety/text:shieldPrompt?api-version={this._apiVersion}");

    public async Task<bool> DetectAttackAsync(PromptShieldRequest request)
    {
        var httpRequest = this.CreateHttpRequest(request);
        var httpResponse = await this._contentSafetyClient.Pipeline.SendRequestAsync(httpRequest, default);

        var httpResponseContent = httpResponse.Content.ToString();

        var response = JsonSerializer.Deserialize<PromptShieldResponse>(httpResponseContent) ??
            throw new Exception("Invalid Prompt Shield response");

        return
            response.UserPromptAnalysis?.AttackDetected is true ||
            response.DocumentsAnalysis?.Any(l => l.AttackDetected) is true;
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
