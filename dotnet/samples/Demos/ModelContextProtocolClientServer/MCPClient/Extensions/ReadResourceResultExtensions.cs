// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using ModelContextProtocol.Protocol.Types;

namespace MCPClient;

/// <summary>
/// Extension methods for <see cref="ReadResourceResult"/>.
/// </summary>
public static class ReadResourceResultExtensions
{
    /// <summary>
    /// Converts a <see cref="ReadResourceResult"/> to a <see cref="ChatMessageContentItemCollection"/>.
    /// </summary>
    /// <param name="readResourceResult">The MCP read resource result to convert.</param>
    /// <returns>The corresponding <see cref="ChatMessageContentItemCollection"/>.</returns>
    public static ChatMessageContentItemCollection ToChatMessageContentItemCollection(this ReadResourceResult readResourceResult)
    {
        if (readResourceResult.Contents.Count == 0)
        {
            throw new InvalidOperationException("The resource does not contain any contents.");
        }

        ChatMessageContentItemCollection result = [];

        foreach (var resourceContent in readResourceResult.Contents)
        {
            Dictionary<string, object?> metadata = new()
            {
                ["uri"] = resourceContent.Uri
            };

            if (resourceContent is TextResourceContents textResourceContent)
            {
                result.Add(new TextContent()
                {
                    Text = textResourceContent.Text,
                    MimeType = textResourceContent.MimeType,
                    Metadata = metadata,
                });
            }
            else if (resourceContent is BlobResourceContents blobResourceContent)
            {
                if (blobResourceContent.MimeType?.StartsWith("image", System.StringComparison.InvariantCulture) ?? false)
                {
                    result.Add(new ImageContent()
                    {
                        Data = Convert.FromBase64String(blobResourceContent.Blob),
                        MimeType = blobResourceContent.MimeType,
                        Metadata = metadata,
                    });
                }
                else if (blobResourceContent.MimeType?.StartsWith("audio", System.StringComparison.InvariantCulture) ?? false)
                {
                    result.Add(new AudioContent
                    {
                        Data = Convert.FromBase64String(blobResourceContent.Blob),
                        MimeType = blobResourceContent.MimeType,
                        Metadata = metadata,
                    });
                }
                else
                {
                    result.Add(new BinaryContent
                    {
                        Data = Convert.FromBase64String(blobResourceContent.Blob),
                        MimeType = blobResourceContent.MimeType,
                        Metadata = metadata,
                    });
                }
            }
        }

        return result;
    }
}
