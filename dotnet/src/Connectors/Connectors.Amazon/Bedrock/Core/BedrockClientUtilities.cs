// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Linq;
using System.Net;
using System.Text;
using System.Text.Json;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime;
using Amazon.Runtime.Documents;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// Utility functions for the Bedrock clients.
/// </summary>
internal sealed class BedrockClientUtilities
{
    /// <summary>
    /// Convert the Http Status Code in Converse Response to the Activity Status Code for Semantic Kernel activity.
    /// </summary>
    /// <param name="httpStatusCode">The status code</param>
    /// <returns>The ActivityStatusCode for the Semantic Kernel</returns>
    internal static ActivityStatusCode ConvertHttpStatusCodeToActivityStatusCode(HttpStatusCode httpStatusCode)
    {
        if ((int)httpStatusCode >= 200 && (int)httpStatusCode < 300)
        {
            // 2xx status codes represent success
            return ActivityStatusCode.Ok;
        }
        if ((int)httpStatusCode >= 400 && (int)httpStatusCode < 600)
        {
            // 4xx and 5xx status codes represent errors
            return ActivityStatusCode.Error;
        }
        // Any other status code is considered unset
        return ActivityStatusCode.Unset;
    }

    /// <summary>
    /// Map Conversation role (value) to author role to build message content for semantic kernel output.
    /// </summary>
    /// <param name="role">The ConversationRole in string form to convert to AuthorRole</param>
    /// <returns>The corresponding AuthorRole.</returns>
    /// <exception cref="ArgumentOutOfRangeException">Thrown if invalid role</exception>
    internal static AuthorRole MapConversationRoleToAuthorRole(string role)
    {
        return role.ToUpperInvariant() switch
        {
            "USER" => AuthorRole.User,
            "ASSISTANT" => AuthorRole.Assistant,
            "SYSTEM" => AuthorRole.System,
            _ => throw new ArgumentOutOfRangeException(nameof(role), $"Invalid role: {role}")
        };
    }

    internal static void BedrockServiceClientRequestHandler(object sender, RequestEventArgs e)
    {
        if (e is not WebServiceRequestEventArgs args || !args.Headers.TryGetValue("User-Agent", out string? value) || value.Contains(HttpHeaderConstant.Values.UserAgent))
        {
            return;
        }
        args.Headers["User-Agent"] = $"{value} {HttpHeaderConstant.Values.UserAgent}";
        args.Headers[HttpHeaderConstant.Names.SemanticKernelVersion] = HttpHeaderConstant.Values.GetAssemblyVersion(typeof(BedrockClientUtilities));
    }

    private static object? ConvertDocument(Document document, bool throwErrorIfUnknown = false)
    {
        if (document.IsString())
        {
            return document.AsString();
        }

        if (document.IsInt())
        {
            return document.AsInt();
        }

        if (document.IsLong())
        {
            return document.AsLong();
        }

        if (document.IsBool())
        {
            return document.AsBool();
        }

        if (document.IsDouble())
        {
            return document.AsDouble();
        }

        if (document.IsNull())
        {
            return null;
        }

        if (document.IsList())
        {
            return document.AsList().Select(x => ConvertDocument(x)).ToArray();
        }

        if (document.IsDictionary())
        {
            return document.AsDictionary().ToDictionary(kv => kv.Key, kv => ConvertDocument(kv.Value));
        }

        if (throwErrorIfUnknown)
        {
            throw new NotSupportedException("Unsupported Document type");
        }

        return null;
    }

    private static ImageContent ConvertImageBlock(ImageBlock imageBlock)
    {
        var mimeType = "application/octetstream";
        if (imageBlock.Format == ImageFormat.Gif)
        {
            mimeType = "image/gif";
        }
        else if (imageBlock.Format == ImageFormat.Jpeg)
        {
            mimeType = "image/jpeg";
        }
        else if (imageBlock.Format == ImageFormat.Png)
        {
            mimeType = "image/png";
        }
        else if (imageBlock.Format == ImageFormat.Webp)
        {
            mimeType = "image/webp";
        }
        return new ImageContent(imageBlock.Source.Bytes.ToArray(), mimeType);
    }

    private static BinaryContent ConvertVideoBlock(VideoBlock videoBlock)
    {
        // Video is not an explicitly supported content type, so just return it as binary content for now
        var mimeType = "application/octetstream";
        if (videoBlock.Format == VideoFormat.Mpeg)
        {
            mimeType = "video/mpeg";
        }
        else if (videoBlock.Format == VideoFormat.Mp4)
        {
            mimeType = "video/mp4";
        }
        else if (videoBlock.Format == VideoFormat.Webm)
        {
            mimeType = "video/webm";
        }
        return new BinaryContent(videoBlock.Source.Bytes.ToArray(), mimeType);
    }

    private static KernelContent ConvertDocumentBlock(DocumentBlock documentBlock)
    {
        if (documentBlock.Format == DocumentFormat.Csv || documentBlock.Format == DocumentFormat.Html || documentBlock.Format == DocumentFormat.Md || documentBlock.Format == DocumentFormat.Txt)
        {
            // These formats are supported, so return them as text content
            // Making an assumption that the text is UTF-8 encoded
            var text = Encoding.UTF8.GetString(documentBlock.Source.Bytes.ToArray());
            return new TextContent(text);
        }

        // Binary document is not explicitly supported, so just return it as binary content for now
        var mimeType = "application/octetstream";
        if (documentBlock.Format == DocumentFormat.Pdf)
        {
            mimeType = "application/pdf";
        }
        else if (documentBlock.Format == DocumentFormat.Doc)
        {
            mimeType = "application/msword";
        }
        else if (documentBlock.Format == DocumentFormat.Docx)
        {
            mimeType = "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
        }
        else if (documentBlock.Format == DocumentFormat.Xls)
        {
            mimeType = "application/vnd.ms-excel";
        }
        else if (documentBlock.Format == DocumentFormat.Xlsx)
        {
            mimeType = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
        }
        return new BinaryContent(documentBlock.Source.Bytes.ToArray(), mimeType);
    }

    /// <summary>
    /// Check if the content block can be converted to a KernelContent.
    /// </summary>
    /// <param name="contentBlock">The content block to check.</param>
    /// <returns> True if the content block can be converted, false otherwise.</returns>
    internal static bool CanConvertContentBlock(ContentBlock contentBlock)
    {
        return !string.IsNullOrWhiteSpace(contentBlock.Text) ||
               contentBlock.ToolUse != null ||
               contentBlock.ToolResult != null ||
               contentBlock.Image != null ||
               contentBlock.Video != null ||
               contentBlock.Document != null ||
               contentBlock.ReasoningContent != null;
    }

    /// <summary>
    /// Convert a ContentBlock to a KernelContent.
    /// </summary>
    /// <param name="contentBlock">The content block to convert.</param>
    /// <returns>The converted KernelContent.</returns>
    /// <exception cref="ArgumentException">Thrown if the content block type is not supported.</exception>
    internal static KernelContent ConvertContentBlock(ContentBlock contentBlock)
    {
        // contentBlock is a union per spec at
        // https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_ContentBlock.html,
        // so check which one of the attributes are set and add the appropriate content

        // This is roughly ordered in an opinionated WAG on the likelihood of presence,
        // from most to least likely
        if (!string.IsNullOrWhiteSpace(contentBlock.Text))
        {
            return new TextContent(contentBlock.Text);
        }

        if (contentBlock.ToolUse != null)
        {
            var funcName = FunctionName.Parse(contentBlock.ToolUse.Name);
            var args = new KernelArguments();
            foreach (var kv in contentBlock.ToolUse.Input.AsDictionary())
            {
                args[kv.Key] = ConvertDocument(kv.Value);
            }
            return new FunctionCallContent(funcName.Name, funcName.PluginName, contentBlock.ToolUse.ToolUseId, args);
        }

        if (contentBlock.ToolResult != null)
        {
            var result = contentBlock.ToolResult.Content.Select<ToolResultContentBlock, object?>(c =>
            {
                if (!string.IsNullOrWhiteSpace(c.Text))
                {
                    return new TextContent(c.Text);
                }
                if (c.Json.IsDictionary())
                {
                    var jsonObj = ConvertDocument(c.Json);
                    var json = JsonSerializer.Serialize(jsonObj);
                    return new TextContent(json);
                }
                if (c.Image != null)
                {
                    return ConvertImageBlock(c.Image);
                }
                if (c.Video != null)
                {
                    return ConvertVideoBlock(c.Video);
                }
                if (c.Document != null)
                {
                    return ConvertDocumentBlock(c.Document);
                }
                return null;
            }).ToArray();
            return new FunctionResultContent(null, null, contentBlock.ToolResult.ToolUseId, result);
        }

        if (contentBlock.Image != null)
        {
            return ConvertImageBlock(contentBlock.Image);
        }

        if (contentBlock.Video != null)
        {
            return ConvertVideoBlock(contentBlock.Video);
        }

        if (contentBlock.Document != null)
        {
            return ConvertDocumentBlock(contentBlock.Document);
        }

        if (contentBlock.ReasoningContent != null)
        {
            return new TextContent(contentBlock.ReasoningContent.ReasoningText.Text);
        }

        throw new ArgumentException("Content block type is not supported.", nameof(contentBlock));
    }
}
