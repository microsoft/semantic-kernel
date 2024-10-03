// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using OpenAI.Images;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Base class for AI clients that provides common functionality for interacting with OpenAI services.
/// </summary>
internal partial class ClientCore
{
    /// <summary>
    /// Generates an image with the provided configuration.
    /// </summary>
    /// <param name="targetModel">Model identifier</param>
    /// <param name="prompt">Prompt to generate the image</param>
    /// <param name="width">Width of the image</param>
    /// <param name="height">Height of the image</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Url of the generated image</returns>
    internal async Task<string> GenerateImageAsync(
        string? targetModel,
        string prompt,
        int width,
        int height,
        CancellationToken cancellationToken)
    {
        Verify.NotNullOrWhiteSpace(prompt);

        var size = new GeneratedImageSize(width, height);

        var imageOptions = new ImageGenerationOptions()
        {
            Size = size,
            ResponseFormat = GeneratedImageFormat.Uri
        };

        // The model is not required by the OpenAI API and defaults to the DALL-E 2 server-side - https://platform.openai.com/docs/api-reference/images/create#images-create-model.
        // However, considering that the model is required by the OpenAI SDK and the ModelId property is optional, it defaults to DALL-E 2 in the line below.
        targetModel = string.IsNullOrEmpty(targetModel) ? "dall-e-2" : targetModel!;

        ClientResult<GeneratedImage> response = await RunRequestAsync(() => this.Client!.GetImageClient(targetModel).GenerateImageAsync(prompt, imageOptions, cancellationToken)).ConfigureAwait(false);
        var generatedImage = response.Value;

        return generatedImage.ImageUri?.ToString() ?? throw new KernelException("The generated image is not in url format");
    }

    /// <summary>
    /// Generates an image with the provided configuration.
    /// </summary>
    /// <param name="targetModel">Model identifier</param>
    /// <param name="input">The input text content to generate the image</param>
    /// <param name="executionSettings">Execution settings for the image generation</param>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>List of image generated contents</returns>
    internal async Task<IReadOnlyList<ImageContent>> GetImageContentsAsync(
        string targetModel,
        TextContent input,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        // Ensure the input is valid
        Verify.NotNull(input);

        // Convert the generic execution settings to OpenAI-specific settings
        var imageSettings = OpenAITextToImageExecutionSettings.FromExecutionSettings(executionSettings);

        var imageGenerationOptions = new ImageGenerationOptions()
        {
            Size = GetGeneratedImageSize(imageSettings.Size),
            ResponseFormat = GetResponseFormat(imageSettings.ResponseFormat),
            Style = GetGeneratedImageStyle(imageSettings.Style),
            Quality = GetGeneratedImageQuality(imageSettings.Quality),
            EndUserId = imageSettings.EndUserId,
        };

        ClientResult<GeneratedImage> response = await RunRequestAsync(() => this.Client!.GetImageClient(targetModel).GenerateImageAsync(input.Text, imageGenerationOptions, cancellationToken)).ConfigureAwait(false);
        var generatedImage = response.Value;

        List<ImageContent> result = [];
        if (generatedImage.ImageUri is not null)
        {
            result.Add(new ImageContent(uri: generatedImage.ImageUri) { InnerContent = generatedImage });
        }
        else
        {
            result.Add(new ImageContent(generatedImage.ImageBytes, "image/png") { InnerContent = generatedImage });
        }

        return result;
    }

    private static GeneratedImageSize? GetGeneratedImageSize((int Width, int Height)? size)
        => size is null
            ? null
            : new GeneratedImageSize(size.Value.Width, size.Value.Height);

    private static GeneratedImageQuality? GetGeneratedImageQuality(string? quality)
    {
        if (quality is null)
        {
            return null;
        }

        return quality.ToUpperInvariant() switch
        {
            "STANDARD" => GeneratedImageQuality.Standard,
            "HIGH" or "HD" => GeneratedImageQuality.High,
            _ => throw new NotSupportedException($"The provided quality '{quality}' is not supported.")
        };
    }

    private static GeneratedImageStyle? GetGeneratedImageStyle(string? style)
    {
        if (style is null)
        {
            return null;
        }

        return style.ToUpperInvariant() switch
        {
            "VIVID" => GeneratedImageStyle.Vivid,
            "NATURAL" => GeneratedImageStyle.Natural,
            _ => throw new NotSupportedException($"The provided style '{style}' is not supported.")
        };
    }

    private static GeneratedImageFormat? GetResponseFormat(object? responseFormat)
    {
        if (responseFormat is null)
        {
            return null;
        }

        if (responseFormat is GeneratedImageFormat format)
        {
            return format;
        }

        if (responseFormat is string formatString)
        {
            return formatString.ToUpperInvariant() switch
            {
                "URI" or "URL" => GeneratedImageFormat.Uri,
                "BYTES" or "B64_JSON" => GeneratedImageFormat.Bytes,
                _ => throw new NotSupportedException($"The provided response format '{formatString}' is not supported.")
            };
        }

        throw new NotSupportedException($"The provided response format type '{responseFormat.GetType()}' is not supported.");
    }
}
