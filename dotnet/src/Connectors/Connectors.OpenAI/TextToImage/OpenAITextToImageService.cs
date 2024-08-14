// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TextToImage;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// OpenAI text to image service.
/// </summary>
[Experimental("SKEXP0010")]
public sealed class OpenAITextToImageService : ITextToImageService
{
    private readonly OpenAITextToImageClientCore _core;

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
    /// The model to use for image generation.
    /// </summary>
    private readonly string? _modelId;

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAITextToImageService"/> class.
    /// </summary>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="organization">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="modelId">The model to use for image generation.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public OpenAITextToImageService(
        string apiKey,
        string? organization = null,
        string? modelId = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(apiKey);
        this._authorizationHeaderValue = $"Bearer {apiKey}";
        this._organizationHeaderValue = organization;
        this._modelId = modelId;

        this._core = new(httpClient, loggerFactory?.CreateLogger(this.GetType()));
        this._core.AddAttribute(OpenAIClientCore.OrganizationKey, organization);
        if (modelId is not null)
        {
            this._core.AddAttribute(AIServiceExtensions.ModelIdKey, modelId);
        }

        this._core.RequestCreated += (_, request) =>
        {
            request.Headers.Add("Authorization", this._authorizationHeaderValue);
            if (!string.IsNullOrEmpty(this._organizationHeaderValue))
            {
                request.Headers.Add("OpenAI-Organization", this._organizationHeaderValue);
            }
        };
    }

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._core.Attributes;

    /// <inheritdoc/>
    public Task<string> GenerateImageAsync(string description, int width, int height, Kernel? kernel = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(description);
        if (width != height || (width != 256 && width != 512 && width != 1024))
        {
            throw new ArgumentOutOfRangeException(nameof(width), width, "OpenAI can generate only square images of size 256x256, 512x512, or 1024x1024.");
        }

        return this.GenerateImageAsync(this._modelId, description, width, height, "url", x => x.Url, cancellationToken);
    }

    /// <inheritdoc/>
    public async Task<IReadOnlyList<ImageContent>> GetImageContentsAsync(
        TextContent input,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        // Ensure the input is valid
        Verify.NotNull(input);

        // Convert the generic execution settings to OpenAI-specific settings
        var imageSettings = OpenAITextToImageExecutionSettings.FromExecutionSettings(executionSettings);

        // Determine the size of the image based on the width and height settings
        var size = (imageSettings.Width, imageSettings.Height) switch
        {
            (256, 256) => "256x256",
            (512, 512) => "512x512",
            (1024, 1024) => "1024x1024",
            (1792, 1024) => "1792x1024",
            (1024, 1792) => "1024x1792",
            _ => throw new NotSupportedException($"The provided size is not supported: {imageSettings.Width}x{imageSettings.Height}")
        };

        // Validate quality and style
        var supportedQualities = new[] { "standard", "hd" };
        var supportedStyles = new[] { "vivid", "natural" };

        if (!string.IsNullOrEmpty(imageSettings.Quality) && !supportedQualities.Contains(imageSettings.Quality))
        {
            throw new NotSupportedException($"The provided quality '{imageSettings.Quality}' is not supported.");
        }

        if (!string.IsNullOrEmpty(imageSettings.Style) && !supportedStyles.Contains(imageSettings.Style))
        {
            throw new NotSupportedException($"The provided style '{imageSettings.Style}' is not supported.");
        }

        // Create the request body for the image generation
        var requestBody = JsonSerializer.Serialize(new TextToImageRequest
        {
            Model = imageSettings.ModelId ?? this._modelId,
            Prompt = input.Text ?? string.Empty,
            Size = size,
            Count = imageSettings.ImageCount ?? 1,
            Quality = imageSettings.Quality ?? "standard",
            Style = imageSettings.Style ?? "vivid"
        });

        // Execute the request using the core client and return Image objects
        var imageStrings = await this._core.ExecuteImageGenerationRequestAsync(OpenAIEndpoint, requestBody, x => x.Url ?? x.AsBase64, cancellationToken).ConfigureAwait(false);

        // Convert the strings to ImageContent objects
        var images = new List<ImageContent>();
        foreach (var imageString in imageStrings)
        {
            if (Uri.TryCreate(imageString, UriKind.Absolute, out var uriResult) && (uriResult.Scheme == Uri.UriSchemeHttp || uriResult.Scheme == Uri.UriSchemeHttps))
            {
                images.Add(new ImageContent(uriResult));
            }
            else
            {
                images.Add(new ImageContent($"data:;base64,{imageString}"));
            }
        }

        return images.AsReadOnly();
    }

    private async Task<string> GenerateImageAsync(
        string? model,
        string description,
        int width, int height,
        string format, Func<TextToImageResponse.Image, string> extractResponse,
        CancellationToken cancellationToken)
    {
        Verify.NotNull(extractResponse);

        var requestBody = JsonSerializer.Serialize(new TextToImageRequest
        {
            Model = model,
            Prompt = description,
            Size = $"{width}x{height}",
            Count = 1,
            Format = format,
        });

        var list = await this._core.ExecuteImageGenerationRequestAsync(OpenAIEndpoint, requestBody, extractResponse!, cancellationToken).ConfigureAwait(false);
        return list[0];
    }
}
