// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.ImageGeneration;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.CustomClient;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ImageGeneration;
/// <summary>
/// A class for generating images using OpenAI's API.
/// </summary>
public class OpenAIImageGeneration : OpenAIClientBase, IImageGeneration
{
    /// <summary>
    /// OpenAI REST API endpoint
    /// </summary>
    private const string OpenAIEndpoint = "https://api.openai.com/v1/images/generations";

    /// <summary>
    /// Optional value for the OpenAI-Organization header.
    /// </summary>
    private readonly string? _organizationHeaderValue;

    /// <summary>
    /// Value for the authorization header.
    /// </summary>
    private readonly string _authorizationHeaderValue;

    /// <summary>
    /// OpenAI DALL-E 3 Image Generation Options
    /// </summary>
    private readonly DALLE3GenerationOptions? _imageGenerationOptions;

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIImageGeneration"/> class.
    /// </summary>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="organization">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <param name="options">DALL-E 3 image generation options. If not null, the DALL-E 3 model will be used.</param>
    public OpenAIImageGeneration(
        string apiKey,
        string? organization = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null,
        DALLE3GenerationOptions? options = null
    ) : base(httpClient, loggerFactory)
    {
        Verify.NotNullOrWhiteSpace(apiKey);
        this._authorizationHeaderValue = $"Bearer {apiKey}";
        this._organizationHeaderValue = organization;
        this._imageGenerationOptions = options;
        this.AddAttribute(OrganizationKey, organization!);
    }

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, string> Attributes => this.InternalAttributes;

    /// <summary>Adds headers to use for OpenAI HTTP requests.</summary>
    private protected override void AddRequestHeaders(HttpRequestMessage request)
    {
        base.AddRequestHeaders(request);

        request.Headers.Add("Authorization", this._authorizationHeaderValue);
        if (!string.IsNullOrEmpty(this._organizationHeaderValue))
        {
            request.Headers.Add("OpenAI-Organization", this._organizationHeaderValue);
        }
    }

    /// <inheritdoc/>
    public Task<string> GenerateImageAsync(string description, int width, int height, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(description);

        if (this._imageGenerationOptions is not null)
        {
            ImageGenerationVerify.DALL3ImageSize(width, height);
        }
        else
        {
            ImageGenerationVerify.DALLE2ImageSize(width, height);
        }

        return this.GenerateImageAsync(description, width, height, "url", x => x.Url, cancellationToken);
    }

    private async Task<string> GenerateImageAsync(
        string description,
        int width, int height,
        string format, Func<ImageGenerationResponse.Image, string> extractResponse,
        CancellationToken cancellationToken)
    {
        Debug.Assert(format is "url" or "b64_json");
        Debug.Assert(extractResponse is not null);

        var model = this._imageGenerationOptions is not null ? "dall-e-3" : "dall-e-2";

        var requestBody = Microsoft.SemanticKernel.Text.Json.Serialize(new ImageGenerationRequest
        {
            Model = model,
            Prompt = description,
            Size = $"{width}x{height}",
            Count = 1,
            Format = format,
            Quality = this._imageGenerationOptions?.Quality,
            Style = this._imageGenerationOptions?.Style
        });

        var list = await this.ExecuteImageGenerationRequestAsync(OpenAIEndpoint, requestBody, extractResponse!, cancellationToken).ConfigureAwait(false);
        return list[0];
    }
}
