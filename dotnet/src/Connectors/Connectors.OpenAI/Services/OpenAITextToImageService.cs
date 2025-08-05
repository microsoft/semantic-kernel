using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using System.Threading.Tasks;
using System.Threading;
using Microsoft.SemanticKernel.TextToImage;
using Microsoft.SemanticKernel;
using System.IO;


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
public class OpenAITextToImageService : ITextToImageService, IImageToImageService
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
        this._client = new(modelId ?? "dall-e-2", apiKey, organization, null, httpClient, loggerFactory?.CreateLogger(this.GetType()));
    }

    /// <inheritdoc/>
    public Task<IReadOnlyList<Microsoft.SemanticKernel.ImageContent>> GetImageContentsAsync(
        TextContent input,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
        => this._client.GetImageContentsAsync(this._client.ModelId, input, executionSettings, kernel, cancellationToken);

    /// <inheritdoc/>
    public Task<IReadOnlyList<ImageContent>> EditImageAsync(
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

        return this._client.EditImageAsync(
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

    private static string GetFileNameFromStream(Stream stream, string defaultName)
    {
        if (stream is FileStream fileStream)
        {
            return Path.GetFileName(fileStream.Name);
        }
        return defaultName;
    }
}
