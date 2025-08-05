// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.Collections.Generic;
using System.IO;
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
        CancellationToken cancellationToken
    )
    {
        Verify.NotNullOrWhiteSpace(prompt);

        var size = new GeneratedImageSize(width, height);

        var imageOptions = new ImageGenerationOptions()
        {
            Size = size,
            ResponseFormat = GeneratedImageFormat.Uri,
        };

        // The model is not required by the OpenAI API and defaults to the DALL-E 2 server-side - https://platform.openai.com/docs/api-reference/images/create#images-create-model.
        // However, considering that the model is required by the OpenAI SDK and the ModelId property is optional, it defaults to DALL-E 2 in the line below.
        targetModel = string.IsNullOrEmpty(targetModel) ? "dall-e-2" : targetModel!;

        ClientResult<GeneratedImage> response = await RunRequestAsync(() =>
                this.Client!.GetImageClient(targetModel)
                    .GenerateImageAsync(prompt, imageOptions, cancellationToken)
            )
            .ConfigureAwait(false);
        var generatedImage = response.Value;

        return generatedImage.ImageUri?.ToString()
            ?? throw new KernelException("The generated image is not in url format");
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
        CancellationToken cancellationToken = default
    )
    {
        // Ensure the input is valid
        Verify.NotNull(input);

        // Convert the generic execution settings to OpenAI-specific settings
        var imageSettings = OpenAITextToImageExecutionSettings.FromExecutionSettings(
            executionSettings
        );

        // Check if we need to generate multiple images
        int imageCount = imageSettings.NumberOfImages ?? 1;

        if (imageCount < 1)
        {
            throw new ArgumentOutOfRangeException(
                nameof(executionSettings),
                "NumberOfImages must be at least 1"
            );
        }

        var imageGenerationOptions = new ImageGenerationOptions()
        {
            Size = GetGeneratedImageSize(imageSettings.Size),
            ResponseFormat = GetResponseFormat(imageSettings.ResponseFormat),
            Style = GetGeneratedImageStyle(imageSettings.Style),
            Quality = GetGeneratedImageQuality(imageSettings.Quality, targetModel),
            EndUserId = imageSettings.EndUserId,
            ModerationLevel = GetGeneratedImageModerationLevel(imageSettings.Moderation),
            OutputFileFormat = GetGeneratedImageFileFormat(imageSettings.OutputFormat),
            OutputCompressionFactor = imageSettings.OutputCompression,
            Background = GetGeneratedImageBackground(imageSettings.Background),
        };

        List<ImageContent> result = [];

        if (imageCount == 1)
        {
            // Use the single image generation method
            ClientResult<GeneratedImage> response = await RunRequestAsync(() =>
                    this.Client!.GetImageClient(targetModel)
                        .GenerateImageAsync(input.Text, imageGenerationOptions, cancellationToken)
                )
                .ConfigureAwait(false);

            var generatedImage = response.Value;
            AddGeneratedImageToResult(generatedImage, result);
        }
        else
        {
            // Use the multiple images generation method
            ClientResult<GeneratedImageCollection> response = await RunRequestAsync(() =>
                    this.Client!.GetImageClient(targetModel)
                        .GenerateImagesAsync(
                            input.Text,
                            imageCount,
                            imageGenerationOptions,
                            cancellationToken
                        )
                )
                .ConfigureAwait(false);

            var generatedImages = response.Value;
            foreach (var generatedImage in generatedImages)
            {
                AddGeneratedImageToResult(generatedImage, result);
            }
        }

        return result;
    }

    private static void AddGeneratedImageToResult(
        GeneratedImage generatedImage,
        List<ImageContent> result
    )
    {
        if (generatedImage.ImageUri is not null)
        {
            result.Add(
                new ImageContent(uri: generatedImage.ImageUri) { InnerContent = generatedImage }
            );
        }
        else if (generatedImage.ImageBytes is not null)
        {
            result.Add(
                new ImageContent(generatedImage.ImageBytes, "image/png")
                {
                    InnerContent = generatedImage,
                }
            );
        }
    }

    /// <summary>
    /// Generates multiple images with the provided configuration.
    /// </summary>
    /// <param name="targetModel">Model identifier</param>
    /// <param name="input">The input text content to generate the images</param>
    /// <param name="imageCount">Number of images to generate</param>
    /// <param name="executionSettings">Execution settings for the image generation</param>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>List of generated image contents</returns>
    internal async Task<IReadOnlyList<ImageContent>> GenerateImagesAsync(
        string targetModel,
        TextContent input,
        int imageCount,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default
    )
    {
        // Ensure the input is valid
        Verify.NotNull(input);

        if (imageCount < 1)
        {
            throw new ArgumentOutOfRangeException(
                nameof(imageCount),
                "Image count must be at least 1"
            );
        }

        // Convert the generic execution settings to OpenAI-specific settings
        var imageSettings = OpenAITextToImageExecutionSettings.FromExecutionSettings(
            executionSettings
        );

        var imageGenerationOptions = new ImageGenerationOptions()
        {
            Size = GetGeneratedImageSize(imageSettings.Size),
            ResponseFormat = GetResponseFormat(imageSettings.ResponseFormat),
            Style = GetGeneratedImageStyle(imageSettings.Style),
            Quality = GetGeneratedImageQuality(imageSettings.Quality, targetModel),
            EndUserId = imageSettings.EndUserId,
            ModerationLevel = GetGeneratedImageModerationLevel(imageSettings.Moderation),
            OutputFileFormat = GetGeneratedImageFileFormat(imageSettings.OutputFormat),
            OutputCompressionFactor = imageSettings.OutputCompression,
            Background = GetGeneratedImageBackground(imageSettings.Background),
        };

        List<ImageContent> result = [];

        if (imageCount == 1)
        {
            // Use the single image generation method
            ClientResult<GeneratedImage> response = await RunRequestAsync(() =>
                    this.Client!.GetImageClient(targetModel)
                        .GenerateImageAsync(input.Text, imageGenerationOptions, cancellationToken)
                )
                .ConfigureAwait(false);

            var generatedImage = response.Value;
            AddGeneratedImageToResult(generatedImage, result);
        }
        else
        {
            // Use the multiple images generation method
            ClientResult<GeneratedImageCollection> response = await RunRequestAsync(() =>
                    this.Client!.GetImageClient(targetModel)
                        .GenerateImagesAsync(
                            input.Text,
                            imageCount,
                            imageGenerationOptions,
                            cancellationToken
                        )
                )
                .ConfigureAwait(false);

            var generatedImages = response.Value;
            foreach (var generatedImage in generatedImages)
            {
                AddGeneratedImageToResult(generatedImage, result);
            }
        }

        return result;
    }

    /// <summary>
    /// Generates an edited image based on a prompt and optional mask.
    /// </summary>
    internal async Task<IReadOnlyList<ImageContent>> GenerateEditImageAsync(
        string targetModel,
        Stream image,
        string imageFileName,
        string prompt,
        Stream? mask,
        string? maskFileName,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default
    )
    {
        // Ensure the inputs are valid
        Verify.NotNull(image);
        Verify.NotNullOrWhiteSpace(imageFileName);
        Verify.NotNullOrWhiteSpace(prompt);

        // Convert the generic execution settings to OpenAI-specific settings
        var imageSettings = OpenAITextToImageExecutionSettings.FromExecutionSettings(
            executionSettings
        );

        var imageEditOptions = new ImageEditOptions()
        {
            Size = GetGeneratedImageSize(imageSettings.Size),
            ResponseFormat = GetResponseFormat(imageSettings.ResponseFormat),
            EndUserId = imageSettings.EndUserId,
        };

        List<ImageContent> result = [];

        // Check if we need to generate multiple images
        int imageCount = imageSettings.NumberOfImages ?? 1;

        if (imageCount == 1)
        {
            ClientResult<GeneratedImage> response;

            if (mask is null)
            {
                // Use the image with transparency as mask
                response = await RunRequestAsync(() =>
                        this.Client!.GetImageClient(targetModel)
                            .GenerateImageEditAsync(
                                image,
                                imageFileName,
                                prompt,
                                imageEditOptions,
                                cancellationToken
                            )
                    )
                    .ConfigureAwait(false);
            }
            else
            {
                // Use the provided mask
                response = await RunRequestAsync(() =>
                        this.Client!.GetImageClient(targetModel)
                            .GenerateImageEditAsync(
                                image,
                                imageFileName,
                                prompt,
                                mask,
                                maskFileName!,
                                imageEditOptions,
                                cancellationToken
                            )
                    )
                    .ConfigureAwait(false);
            }

            var generatedImage = response.Value;
            AddGeneratedImageToResult(generatedImage, result);
        }
        else
        {
            ClientResult<GeneratedImageCollection> response;

            if (mask is null)
            {
                // Use the image with transparency as mask
                response = await RunRequestAsync(() =>
                        this.Client!.GetImageClient(targetModel)
                            .GenerateImageEditsAsync(
                                image,
                                imageFileName,
                                prompt,
                                imageCount,
                                imageEditOptions,
                                cancellationToken
                            )
                    )
                    .ConfigureAwait(false);
            }
            else
            {
                // Use the provided mask
                response = await RunRequestAsync(() =>
                        this.Client!.GetImageClient(targetModel)
                            .GenerateImageEditsAsync(
                                image,
                                imageFileName,
                                prompt,
                                mask,
                                maskFileName!,
                                imageCount,
                                imageEditOptions,
                                cancellationToken
                            )
                    )
                    .ConfigureAwait(false);
            }

            var generatedImages = response.Value;
            foreach (var generatedImage in generatedImages)
            {
                AddGeneratedImageToResult(generatedImage, result);
            }
        }

        return result;
    }

    private static GeneratedImageSize? GetGeneratedImageSize((int Width, int Height)? size) =>
        size is null ? null : new GeneratedImageSize(size.Value.Width, size.Value.Height);

    private static GeneratedImageQuality? GetGeneratedImageQuality(object? quality, string? modelId)
    {
        if (quality is null)
        {
            return null;
        }

        if (quality is GeneratedImageQuality imageQuality)
        {
            return imageQuality;
        }

        if (quality is string qualityString)
        {
            var isGptImage1 =
                modelId?.Equals("gpt-image-1", StringComparison.OrdinalIgnoreCase) ?? false;
            var upperQuality = qualityString.ToUpperInvariant();

            if (isGptImage1)
            {
                // GPT-Image-1 uses low/medium/high values
                // Create a new GeneratedImageQuality with the exact string value
                return new GeneratedImageQuality(qualityString.ToLowerInvariant());
            }

            // DALL-E models use standard/hd
            return upperQuality switch
            {
                "STANDARD" => GeneratedImageQuality.Standard,
                "HIGH" or "HD" => GeneratedImageQuality.High,
                _ => throw new NotSupportedException(
                    $"The provided quality '{qualityString}' is not supported for model '{modelId}'."
                ),
            };
        }

        throw new NotSupportedException(
            $"The provided quality type '{quality.GetType()}' is not supported."
        );
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
            _ => throw new NotSupportedException($"The provided style '{style}' is not supported."),
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
                _ => throw new NotSupportedException(
                    $"The provided response format '{formatString}' is not supported."
                ),
            };
        }

        throw new NotSupportedException(
            $"The provided response format type '{responseFormat.GetType()}' is not supported."
        );
    }

    private static GeneratedImageModerationLevel? GetGeneratedImageModerationLevel(
        object? moderation
    )
    {
        if (moderation is null)
        {
            return null;
        }

        if (moderation is GeneratedImageModerationLevel moderationLevel)
        {
            return moderationLevel;
        }

        if (moderation is string moderationString)
        {
            // Create a new GeneratedImageModerationLevel with the exact string value
            return new GeneratedImageModerationLevel(moderationString.ToLowerInvariant());
        }

        throw new NotSupportedException(
            $"The provided moderation type '{moderation.GetType()}' is not supported."
        );
    }

    private static GeneratedImageFileFormat? GetGeneratedImageFileFormat(object? format)
    {
        if (format is null)
        {
            return null;
        }

        if (format is GeneratedImageFileFormat fileFormat)
        {
            return fileFormat;
        }

        if (format is string formatString)
        {
            // You can add more supported formats here if needed
            return new GeneratedImageFileFormat(formatString.ToLowerInvariant());
        }

        throw new NotSupportedException(
            $"The provided file format type '{format.GetType()}' is not supported."
        );
    }

    private static GeneratedImageBackground? GetGeneratedImageBackground(object? background)
    {
        if (background is null)
        {
            return null;
        }

        if (background is GeneratedImageBackground imageBackground)
        {
            return imageBackground;
        }

        if (background is string backgroundString)
        {
            // Create a new GeneratedImageBackground with the exact string value
            return new GeneratedImageBackground(backgroundString.ToLowerInvariant());
        }

        throw new NotSupportedException(
            $"The provided background type '{background.GetType()}' is not supported."
        );
    }
}
