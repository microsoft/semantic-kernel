// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.ImageGeneration;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.CustomClient;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ImageGeneration;

public class OpenAIImageGeneration : OpenAIClientBase, IImageGeneration
{
    // 3P OpenAI REST API endpoint
    private const string OpenAIEndpoint = "https://api.openai.com/v1/images/generations";

    /// <summary>
    /// Create a new instance of OpenAI image generation service
    /// </summary>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="organization">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">Application logger</param>
    public OpenAIImageGeneration(
        string apiKey,
        string? organization = null,
        HttpClient? httpClient = null,
        ILogger? logger = null
    ) : base(httpClient, logger)
    {
        Verify.NotNullOrWhiteSpace(apiKey);
        this.HTTPClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", apiKey);

        if (!string.IsNullOrEmpty(organization))
        {
            this.HTTPClient.DefaultRequestHeaders.Add("OpenAI-Organization", organization);
        }
    }

    /// <inheritdoc/>
    public Task<string> GenerateImageAsync(string description, int width, int height, CancellationToken cancellationToken = default)
    {
        if (width != height || (width != 256 && width != 512 && width != 1024))
        {
            throw new AIException(AIException.ErrorCodes.InvalidRequest, "OpenAI can generate only square images 256x256, 512x512, 1024x1024");
        }

        return this.GenerateImageUrlAsync(description, width, height, cancellationToken);
    }

    private async Task<string> GenerateImageUrlAsync(string description, int width, int height, CancellationToken cancellationToken = default)
    {
        var requestBody = Json.Serialize(new ImageGenerationRequest
        {
            Prompt = description,
            Size = $"{width}x{height}",
            Count = 1,
            Format = "url",
        });

        var list = await this.ExecuteImageUrlGenerationRequestAsync(OpenAIEndpoint, requestBody, cancellationToken).ConfigureAwait(false);
        return list.First();
    }

    private async Task<string> GenerateImageBase64Async(string description, int width, int height, CancellationToken cancellationToken = default)
    {
        var requestBody = Json.Serialize(new ImageGenerationRequest
        {
            Prompt = description,
            Size = $"{width}x{height}",
            Count = 1,
            Format = "b64_json",
        });

        var list = await this.ExecuteImageBase64GenerationRequestAsync(OpenAIEndpoint, requestBody, cancellationToken).ConfigureAwait(false);
        return list.First();
    }
}
