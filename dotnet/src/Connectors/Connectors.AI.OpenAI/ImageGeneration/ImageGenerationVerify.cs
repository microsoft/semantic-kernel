// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Runtime.CompilerServices;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ImageGeneration;
internal static class ImageGenerationVerify
{
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    internal static void DALLE2ImageSize(int width, int height)
    {
        var size = $"{width}x{height}";

        switch (size)
        {
            case "256x256":
            case "512x512":
            case "1024x1024":
                break;
            default:
                throw new ArgumentOutOfRangeException("width or height", size, "OpenAI DALL-E 2 can generate only square images of size 256x256, 512x512 or 1024x1024.");
        }
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    internal static void DALL3ImageSize(int width, int height)
    {
        var size = $"{width}x{height}";

        switch (size)
        {
            case "1792x1024":
            case "1024x1792":
            case "1024x1024":
                break;
            default:
                throw new ArgumentOutOfRangeException("width or height", size, "OpenAI DALL-E 3 can generate only images of size 1792x1024, 1024x1792 or 1024x1024.");
        }
    }
}
