// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel;
using ModelContextProtocol.Protocol;

namespace MCPClient;

/// <summary>
/// Extension methods for the <see cref="ContentBlock"/> class.
/// </summary>
public static class ContentBlockExtensions
{
    /// <summary>
    /// Converts a <see cref="ContentBlock"/> object to a <see cref="KernelContent"/> object.
    /// </summary>
    /// <param name="content">The <see cref="ContentBlock"/> object to convert.</param>
    /// <returns>The corresponding <see cref="KernelContent"/> object.</returns>
    public static KernelContent ToKernelContent(this ContentBlock content)
    {
        return content switch
        {
            TextContentBlock textContentBlock => new TextContent(textContentBlock.Text),
            ImageContentBlock imageContentBlock => new ImageContent(Convert.FromBase64String(imageContentBlock.Data!), imageContentBlock.MimeType),
            AudioContentBlock audioContentBlock => new AudioContent(Convert.FromBase64String(audioContentBlock.Data!), audioContentBlock.MimeType),
            _ => throw new InvalidOperationException($"Unexpected message content type '{content.Type}'"),
        };
    }
}
