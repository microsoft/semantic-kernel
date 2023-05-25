// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.ImageGeneration;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.CustomClient;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ImageGeneration;
public class AzureOpenAIImageGeneration : OpenAIClientBase, IImageGeneration
{
    private readonly string _endpoint;
    private readonly string _apiKey;

    public AzureOpenAIImageGeneration(string endpoint, string apiKey, HttpClient? httpClient = null, ILogger? logger = null) : base(httpClient, logger)
    {
        this._endpoint = $"{endpoint}dalle/text-to-image?api-version=2022-08-03-preview";
        this._apiKey = apiKey;
    }

    public async Task<string> GenerateImageAsync(string description, int width, int height, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(description);
        if (width != height || (width != 256 && width != 512 && width != 1024))
        {
            throw new ArgumentOutOfRangeException(nameof(width), width, "OpenAI can generate only square images of size 256x256, 512x512, or 1024x1024.");
        }
        var requestBody = Json.Serialize(new AzureImageGenerationRequest()
        {
            Caption = description,
            Resolution = $"{width}x{height}"
        });
        var result = await this.EnsureImageGenerationAsync(this._endpoint, requestBody, cancellationToken).ConfigureAwait(false);
        if (result.Result == null)
        {
            throw new AIException(AIException.ErrorCodes.InvalidResponseContent, "Response JSON parse error");
        }
        return result.Result.ContentUrl;
    }
    private async Task<AzureImageGenerationResponse> EnsureImageGenerationAsync(string url, string? requestBody, CancellationToken cancellationToken = default)
    {
        HttpResponseMessage? response = null;
        try
        {
            if (requestBody == null)
            {
                response = await this.ExecuteRequestAsync(url, HttpMethod.Get, null, cancellationToken).ConfigureAwait(false);
            }
            else
            {
                using (var content = new StringContent(requestBody, Encoding.UTF8, "application/json"))
                {
                    response = await this.ExecuteRequestAsync(url, HttpMethod.Post, content, cancellationToken).ConfigureAwait(false);
                }
            }
            var responseJson = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
            var result = this.JsonDeserialize<AzureImageGenerationResponse>(responseJson);
            if (result.Status != "Succeeded")
            {
                if (!response.Headers.TryGetValues("operation-location", out var locationValues) || string.IsNullOrWhiteSpace(locationValues.FirstOrDefault()))
                {
                    throw new AIException(AIException.ErrorCodes.InvalidResponseContent, "Not found operation-location");
                }
                var operationLocation = locationValues.First();
                if (response.Headers.TryGetValues("retry-after", out var retryValues))
                {
                    var retryValue = retryValues.FirstOrDefault();
                    if (int.TryParse(retryValue, out var retry))
                    {
                        await Task.Delay(TimeSpan.FromSeconds(retry), cancellationToken).ConfigureAwait(false);
                    }
                }
                return await this.EnsureImageGenerationAsync(operationLocation, null, cancellationToken).ConfigureAwait(false);
            }
            return result;
        }
        finally
        {
            response?.Dispose();
        }
    }

    private protected override void AddRequestHeaders(HttpRequestMessage request)
    {
        request.Headers.Add("api-key", this._apiKey);
    }
}
