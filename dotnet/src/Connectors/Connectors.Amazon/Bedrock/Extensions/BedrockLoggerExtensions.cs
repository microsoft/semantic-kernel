// Copyright (c) Microsoft. All rights reserved.

using System;
using Amazon.BedrockRuntime.Model;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Extensions;

internal static class BedrockLoggerExtensions
{
    internal static void LogRequest(this ILogger logger, ConverseRequest request, LogLevel logLevel = LogLevel.Information)
    {
        var mi = 0;
        foreach (var m in request.Messages)
        {
            logger.Log(logLevel, "MESSAGE {Index}: {Name}", mi, m.Role.Value);
            var ci = 0;
            foreach (var c in m.Content)
            {
                if (!string.IsNullOrWhiteSpace(c.Text))
                {
                    logger.Log(logLevel, "MESSAGE {Index}: CONTENT {ContentIndex}: TEXT '{Text}'", mi, ci, c.Text);
                }
                else if (c.ToolUse != null)
                {
                    logger.Log(logLevel, "MESSAGE {Index}: CONTENT {ContentIndex}: TOOL USE: {ToolUseName} {ToolUseId}", mi, ci, c.ToolUse.Name, c.ToolUse.ToolUseId);
                }
                else if (c.ToolResult != null)
                {
                    logger.Log(logLevel, "MESSAGE {Index}: CONTENT {ContentIndex}: TOOL RESULT: {ToolResultId} {ToolResultStatus}", mi, ci, c.ToolResult.ToolUseId, c.ToolResult.Status.Value);
                    var tri = 0;
                    foreach (var t in c.ToolResult.Content)
                    {
                        if (!string.IsNullOrWhiteSpace(t.Text))
                        {
                            logger.Log(logLevel, "MESSAGE {Index}: CONTENT {ContentIndex}: TOOL RESULT ITEM {ToolResultItemIndex}: TEXT LENGTH {Length} CHARS '{Text}...'", mi, ci, tri, t.Text.Length, t.Text[..Math.Min(t.Text.Length, 50)]);
                        }
                        else if (t.Document != null)
                        {
                            logger.Log(logLevel, "MESSAGE {Index}: CONTENT {ContentIndex}: TOOL RESULT ITEM {ToolResultItemIndex}: DOCUMENT '{Name}' {Format} {Length} BYTES", mi, ci, tri, t.Document.Name, t.Document.Format.Value, t.Document.Source.Bytes.Length);
                        }
                        else if (!t.Json.IsNull())
                        {
                            logger.Log(logLevel, "MESSAGE {Index}: CONTENT {ContentIndex}: TOOL RESULT ITEM {ToolResultItemIndex}: JSON '{Json}'", mi, ci, tri, t.Json);
                        }
                        else if (t.Image != null)
                        {
                            logger.Log(logLevel, "MESSAGE {Index}: CONTENT {ContentIndex}: TOOL RESULT ITEM {ToolResultItemIndex}: IMAGE {Format} {Length} BYES", mi, ci, tri, t.Image.Format.Value, t.Image.Source.Bytes.Length);
                        }
                        else if (t.Video != null)
                        {
                            logger.Log(logLevel, "MESSAGE {Index}: CONTENT {ContentIndex}: TOOL RESULT ITEM {ToolResultItemIndex}: VIDEO {Format} {Length} BYTES", mi, ci, tri, t.Video.Format.Value, t.Video.Source.Bytes.Length);
                        }
                        else
                        {
                            logger.Log(logLevel, "MESSAGE {Index}: CONTENT {ContentIndex}: TOOL RESULT ITEM {ToolResultItemIndex}: EMPTY", mi, ci, tri);
                        }
                        tri++;
                    }
                }
                else if (c.ReasoningContent != null)
                {
                    logger.Log(logLevel, "MESSAGE {Index}: CONTENT {ContentIndex}: REASONING CONTENT: '{ReasoningText}' {RedactedLength} BYTES", mi, ci, c.ReasoningContent.ReasoningText, c.ReasoningContent.RedactedContent.Length);
                }
                else if (c.Document != null)
                {
                    logger.Log(logLevel, "MESSAGE {Index}: CONTENT {ContentIndex}: DOCUMENT '{Name}' {Format} {Length} BYTES", mi, ci, c.Document.Name, c.Document.Format.Value, c.Document.Source.Bytes.Length);
                }
                else if (c.Image != null)
                {
                    logger.Log(logLevel, "MESSAGE {Index}: CONTENT {ContentIndex}: IMAGE {Format} {Length} BYTES", mi, ci, c.Image.Format.Value, c.Image.Source.Bytes.Length);
                }
                else if (c.Video != null)
                {
                    logger.Log(logLevel, "MESSAGE {Index}: CONTENT {ContentIndex}: VIDEO {Format} {Length} BYTES", mi, ci, c.Video.Format.Value, c.Video.Source.Bytes.Length);
                }
                else if (c.GuardContent != null)
                {
                    if (c.GuardContent.Text != null)
                    {
                        logger.Log(logLevel, "MESSAGE {Index}: CONTENT {ContentIndex}: GUARD CONTENT TEXT '{Text}' QUALIFIERS {Qualifiers}", mi, ci, c.GuardContent.Text, string.Join(", ", c.GuardContent.Text.Qualifiers));
                    }
                    else if (c.GuardContent.Image != null)
                    {
                        logger.Log(logLevel, "MESSAGE {Index}: CONTENT {ContentIndex}: GUARD CONTENT IMAGE {Format} {Length} BYTES", mi, ci, c.GuardContent.Image.Format.Value, c.GuardContent.Image.Source.Bytes.Length);
                    }
                    else
                    {
                        logger.Log(logLevel, "MESSAGE {Index}: CONTENT {ContentIndex}: GUARD CONTENT EMPTY", mi, ci);
                    }
                }
                else
                {
                    logger.Log(logLevel, "MESSAGE {Index}: CONTENT {ContentIndex}: EMPTY", mi, ci);
                }
                ci++;
            }
            mi++;
        }
    }
}
