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
    /// <summary>
    /// Constants of success status
    /// </summary>
    private const string SucceededStatus = "SUCCEEDED";

    /// <summary>
    /// Maximum retry times for the Azure Dall-E API
    /// </summary>
    private const int MaxRetryCount = 5;

    /// <summary>
    /// Default retry wait time in seconds
    /// </summary>
    private const int DefaultRetryAfter = 6;

    /// <summary>
    /// Azure OpenAI REST API endpoint
    /// </summary>
    private readonly string _endpoint;

    /// <summary>
    /// Azure OpenAI API key
    /// </summary>
    private readonly string _apiKey;

    /// <summary>
    /// Create a new instance of Azure OpenAI image generation service
    /// </summary>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">Application logger</param>
    public AzureOpenAIImageGeneration(string endpoint, string apiKey, HttpClient? httpClient = null, ILogger? logger = null) : base(httpClient, logger)
    {
        this._endpoint = $"{endpoint}openai/images/generations:submit?api-version=2023-06-01-preview";
        this._apiKey = apiKey;
    }

    /// <inheritdoc/>
    public async Task<string> GenerateImageAsync(string description, int width, int height, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(description);
        if (width != height || (width != 256 && width != 512 && width != 1024))
        {
            throw new ArgumentOutOfRangeException(nameof(width), width, "OpenAI can generate only square images of size 256x256, 512x512, or 1024x1024.");
        }

        var requestBody = Json.Serialize(new ImageGenerationRequest
        {
            Prompt = description,
            Size = $"{width}x{height}",
            Count = 1
        });

        var result = await this.GetImageGenerationAsync(this._endpoint, requestBody, cancellationToken).ConfigureAwait(false);
        if (result.Result == null)
        {
            throw new AIException(AIException.ErrorCodes.InvalidResponseContent, "Response not contains result");
        }

        return result.Result.Images[0].Url;
    }

    private async Task<AzureImageGenerationResponse> GetImageGenerationAsync(string url, string? requestBody, CancellationToken cancellationToken = default)
    {
        HttpResponseMessage? response = null;
        var retryCount = 0;
        try
        {
            using (var content = new StringContent(requestBody, Encoding.UTF8, "application/json"))
            {
                response = await this.ExecuteRequestAsync(url, HttpMethod.Post, content, cancellationToken).ConfigureAwait(false);
            }

            var responseJson = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
            var result = this.JsonDeserialize<AzureImageGenerationResponse>(responseJson);

            if (!response.Headers.TryGetValues("operation-location", out var locationValues) || string.IsNullOrWhiteSpace(locationValues.FirstOrDefault()))
            {
                throw new AIException(AIException.ErrorCodes.InvalidResponseContent, "Not found operation-location");
            }

            var operationLocation = locationValues.First();
            while (true)
            {
                if (result.Status.Equals(SucceededStatus, StringComparison.OrdinalIgnoreCase))
                {
                    return result;
                }

                if (MaxRetryCount == retryCount)
                {
                    throw new AIException(AIException.ErrorCodes.RequestTimeout, "Reached maximum retry attempts");
                }

                if (response.Headers.TryGetValues("retry-after", out var afterValues) && long.TryParse(afterValues.FirstOrDefault(), out var after))
                {
                    await Task.Delay(TimeSpan.FromSeconds(after), cancellationToken).ConfigureAwait(false);
                }
                else
                {
                    await Task.Delay(TimeSpan.FromSeconds(DefaultRetryAfter), cancellationToken).ConfigureAwait(false);
                }

                response = await this.ExecuteRequestAsync(operationLocation, HttpMethod.Get, null, cancellationToken).ConfigureAwait(false);
                responseJson = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
                result = this.JsonDeserialize<AzureImageGenerationResponse>(responseJson);

                // increase retry count
                retryCount++;
            }
        }
        catch (Exception e) when (e is not AIException)
        {
            throw new AIException(
                AIException.ErrorCodes.UnknownError,
                $"Something went wrong: {e.Message}", e);
        }
        finally
        {
            response?.Dispose();
        }
    }

    /// <summary>Adds headers to use for Azure OpenAI HTTP requests.</summary>
    private protected override void AddRequestHeaders(HttpRequestMessage request)
    {
        request.Headers.Add("api-key", this._apiKey);
    }
}
