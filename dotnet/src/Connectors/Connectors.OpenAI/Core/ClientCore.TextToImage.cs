// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using OpenAI.Images;
using OpenAIImageGenerationOptions = OpenAI.Images.ImageGenerationOptions;

#pragma warning disable MEAI001 // Image generation APIs are experimental.

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
        Verify.NotNull(input);
        string? prompt = input.Text;
        Verify.NotNull(prompt);

        var imageSettings = OpenAITextToImageExecutionSettings.FromExecutionSettings(executionSettings);

        var imageGenerationOptions = new OpenAIImageGenerationOptions()
        {
            Size = GetGeneratedImageSize(imageSettings.Size),
            ResponseFormat = GetResponseFormat(imageSettings.ResponseFormat),
            Style = GetGeneratedImageStyle(imageSettings.Style),
            Quality = GetGeneratedImageQuality(imageSettings.Quality),
            EndUserId = imageSettings.EndUserId,
        };

        var options = new Microsoft.Extensions.AI.ImageGenerationOptions
        {
            Count = 1,
            RawRepresentationFactory = _ => imageGenerationOptions
        };

        using var generator = this.Client!.GetImageClient(targetModel).AsIImageGenerator();
        var response = await RunRequestAsync(() => generator.GenerateAsync(new ImageGenerationRequest(prompt), options, cancellationToken)).ConfigureAwait(false);
        if (response.Contents.Count == 0)
        {
            throw new KernelException("The generated image has no valid content.");
        }

        var generatedImages = response.RawRepresentation as GeneratedImageCollection;

        List<ImageContent> result = new(response.Contents.Count);
        for (int i = 0; i < response.Contents.Count; i++)
        {
            var content = response.Contents[i];
            ImageContent image = content switch
            {
                DataContent data => new(data.Data, data.MediaType),
                UriContent uri => new(uri.Uri) { MimeType = uri.MediaType },
                _ => throw new KernelException("The generated image has no valid content.")
            };

            image.InnerContent = generatedImages is not null ? generatedImages[i] : content.RawRepresentation;
            result.Add(image);
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
            "MEDIUM" => GeneratedImageQuality.MediumQuality,
            "LOW" => GeneratedImageQuality.LowQuality,
            "AUTO" => GeneratedImageQuality.Auto,
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
