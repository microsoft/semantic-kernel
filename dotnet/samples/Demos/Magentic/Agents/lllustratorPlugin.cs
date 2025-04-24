// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.TextToImage;

namespace Magentic.Agents.Internal;

internal sealed class IllustratorPlugin(ITextToImageService imageService)
{
    [KernelFunction]
    [Description("Generate an image from the given description.")]
    public async Task<ImageContent> GenerateImageAsync(string description)
    {
        string imageReference = await imageService.GenerateImageAsync(description, 1024, 1024).ConfigureAwait(false);
        Uri imageUri = new(imageReference);
        return new ImageContent(imageUri);
    }
}
