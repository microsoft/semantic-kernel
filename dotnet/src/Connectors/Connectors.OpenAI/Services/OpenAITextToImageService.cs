// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.TextToImage;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// OpenAI text to image service.
/// </summary>
/// <remarks>
/// Supports multiple image generation models including:
/// - dall-e-2: Original DALL-E model (256x256, 512x512, 1024x1024)
/// - dall-e-3: Enhanced DALL-E model with quality and style options (1024x1024, 1792x1024, 1024x1792)
/// - gpt-image-1: Latest multimodal image generation model with advanced features (1024x1024, 1024x1536, 1536x1024)
/// </remarks>
[Experimental("SKEXP0010")]
public class OpenAITextToImageService : ITextToImageService
{
    private readonly ClientCore _client;

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._client.Attributes;

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAITextToImageService"/> class.
    /// </summary>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="organization">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="modelId">The model to use for image generation. Defaults to "dall-e-2". Supported models: dall-e-2, dall-e-3, gpt-image-1</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public OpenAITextToImageService(
        string apiKey,
        string? organization = null,
        string? modelId = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        this._client = new(
            modelId ?? "dall-e-2",
            apiKey,
            organization,
            null,
            httpClient,
            loggerFactory?.CreateLogger(this.GetType()));
    }

    /// <inheritdoc/>
    public Task<IReadOnlyList<Microsoft.SemanticKernel.ImageContent>> GetImageContentsAsync(
        TextContent input,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default) =>
        this._client.GetImageContentsAsync(
            this._client.ModelId,
            input,
            executionSettings,
            kernel,
            cancellationToken);

    /// <inheritdoc/>
    public Task<IReadOnlyList<ImageContent>> GenerateEditImageAsync(
        Stream image,
        string prompt,
        Stream? mask = null,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        // Determine file names based on stream type or use defaults
        var imageFileName = GetFileNameFromStream(image, "image.png");
        var maskFileName = mask is not null ? GetFileNameFromStream(mask, "mask.png") : null;

        return this._client.GenerateEditImageAsync(
            this._client.ModelId,
            image,
            imageFileName,
            prompt,
            mask,
            maskFileName,
            executionSettings,
            kernel,
            cancellationToken);
    }

    /// <summary>
    /// Generates an edited image based on file paths and a prompt.
    /// </summary>
    /// <param name="imageFilePath">Path to the image file to edit</param>
    /// <param name="prompt">Text prompt describing the desired edits</param>
    /// <param name="maskFilePath">Optional path to mask file indicating areas to edit</param>
    /// <param name="executionSettings">Execution settings for the image edit</param>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>Generated image contents</returns>
    public async Task<IReadOnlyList<ImageContent>> GenerateEditImageAsync(
        string imageFilePath,
        string prompt,
        string? maskFilePath = null,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        using var imageStream = File.OpenRead(imageFilePath);
        
        if (!string.IsNullOrEmpty(maskFilePath))
        {
            using var maskStream = File.OpenRead(maskFilePath);
            return await this.GenerateEditImageAsync(
                imageStream,
                prompt,
                maskStream,
                executionSettings,
                kernel,
                cancellationToken)
                .ConfigureAwait(false);
        }
        
        return await this.GenerateEditImageAsync(
            imageStream,
            prompt,
            null,
            executionSettings,
            kernel,
            cancellationToken)
            .ConfigureAwait(false);
    }

    private static string GetFileNameFromStream(Stream stream, string defaultName)
    {
        if (stream is FileStream fileStream)
        {
            return Path.GetFileName(fileStream.Name);
        }
        return defaultName;
    }
}
