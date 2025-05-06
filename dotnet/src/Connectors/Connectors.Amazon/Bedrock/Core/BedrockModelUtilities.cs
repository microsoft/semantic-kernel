// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.RegularExpressions;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// Utilities class for functions all Bedrock models need to use.
/// </summary>
internal static partial class BedrockModelUtilities
{
    private const string PngMimeType = "image/png";
    private const string JpegMimeType = "image/jpeg";
    private const string GifMimeType = "image/gif";
    private const string WebpMimeType = "image/webp";
    private const string DocMimeType = "application/msword";
    private const string DocxMimeType = "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
    private const string PdfMimeType = "application/pdf";
    private const string XlsMimeType = "application/vnd.ms-excel";
    private const string XlsxMimeType = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
    private const string MpegMimeType = "video/mpeg";
    private const string Mp4MimeType = "video/mp4";
    private const string WebmMimeType = "video/webm";
    private const string ThreeGpMimeType = "video/3gpp";
    private const string MovMimeType = "video/quicktime";

    private static readonly HashSet<string> s_supportedMimeTypes = new()
    {
        PngMimeType,
        JpegMimeType,
        GifMimeType,
        WebpMimeType,
        DocMimeType,
        DocxMimeType,
        PdfMimeType,
        XlsMimeType,
        XlsxMimeType,
        Mp4MimeType,
        MpegMimeType,
        WebmMimeType,
        ThreeGpMimeType,
        MovMimeType
    };

    /// <summary>
    /// Maps the AuthorRole to the corresponding ConversationRole because AuthorRole is static and { readonly get; }. Only called if AuthorRole is User or Assistant (System set outside/beforehand).
    /// </summary>
    /// <param name="role">The AuthorRole to be converted to ConversationRole</param>
    /// <param name="toolResultsPresent">True if tool results are present in the message, false otherwise</param>
    /// <returns>The corresponding ConversationRole</returns>
    /// <exception cref="ArgumentOutOfRangeException">Thrown if invalid role.</exception>
    internal static ConversationRole MapAuthorRoleToConversationRole(AuthorRole role, bool toolResultsPresent = false)
    {
        if (role == AuthorRole.User)
        {
            return ConversationRole.User;
        }

        if (role == AuthorRole.Assistant)
        {
            return ConversationRole.Assistant;
        }

        if (role == AuthorRole.Tool)
        {
            return toolResultsPresent ? ConversationRole.User : ConversationRole.Assistant;
        }

        throw new ArgumentOutOfRangeException($"Invalid role: {role}");
    }

    /// <summary>
    /// Gets the system messages from the ChatHistory and adds them to the ConverseRequest System parameter.
    /// </summary>
    /// <param name="chatHistory">The ChatHistory object to be parsed.</param>
    /// <returns>The list of SystemContentBlock for the converse request.</returns>
    internal static List<SystemContentBlock> GetSystemMessages(ChatHistory chatHistory)
    {
        return chatHistory
            .Where(m => m.Role == AuthorRole.System)
            .Select(m => new SystemContentBlock { Text = m.Content })
            .ToList();
    }

    private static bool IsContentSupported(KernelContent content)
    {
        return content is TextContent ||
               content is FunctionCallContent ||
               content is FunctionResultContent ||
               (content is ImageContent image && (image.DataUri != null || image.Uri != null)) ||
               (content is PdfContent pdf && (pdf.DataUri != null || pdf.Uri != null)) ||
               (content is DocContent doc && (doc.DataUri != null || doc.Uri != null)) ||
               (content is DocxContent docx && (docx.DataUri != null || docx.Uri != null));
    }

    private static ImageFormat MimeTypeToImageFormat(string? mimeType)
    {
        return mimeType switch
        {
            "image/png" => ImageFormat.Png,
            "image/jpeg" => ImageFormat.Jpeg,
            "image/gif" => ImageFormat.Gif,
            "image/webp" => ImageFormat.Webp,
            _ => throw new InvalidOperationException($"Unsupported image format: '{mimeType}'")
        };
    }

    private static ToolResultContentBlock CreateImageContentBlock(ImageFormat format, byte[] data)
    {
        return new ToolResultContentBlock
        {
            Image = new ImageBlock
            {
                Format = format,
                Source = new ImageSource
                {
                    Bytes = new MemoryStream(data)
                }
            }
        };
    }
    private static ToolResultContentBlock CreateDocumentContentBlock(DocumentFormat format, byte[] data)
    {
        return new ToolResultContentBlock
        {
            Document = new DocumentBlock
            {
                Format = format,
                Name = $"document-{Guid.NewGuid()}", // NOTE: Random generated name
                Source = new DocumentSource
                {
                    Bytes = new MemoryStream(data)
                }
            }
        };
    }

    private static ToolResultContentBlock CreateVideoContentBlock(VideoFormat format, byte[] data)
    {
        return new ToolResultContentBlock
        {
            Video = new VideoBlock
            {
                Format = format,
                Source = new VideoSource
                {
                    Bytes = new MemoryStream(data)
                }
            }
        };
    }

    private static IEnumerable<ToolResultContentBlock> ConvertResultToToolResultContentBlocks(object? result)
    {
        if (result is string text)
        {
            var match = DataUriRegex().Match(text);
            if (match.Groups.Count >= 3 && s_supportedMimeTypes.Contains(match.Groups["type"].Value))
            {
                var data = match.Groups["data"].Value;
                var bytes = Convert.FromBase64String(data);
                yield return match.Groups["type"].Value switch
                {
                    PngMimeType => CreateImageContentBlock(ImageFormat.Png, bytes),
                    JpegMimeType => CreateImageContentBlock(ImageFormat.Jpeg, bytes),
                    GifMimeType => CreateImageContentBlock(ImageFormat.Gif, bytes),
                    WebpMimeType => CreateImageContentBlock(ImageFormat.Webp, bytes),
                    DocMimeType => CreateDocumentContentBlock(DocumentFormat.Doc, bytes),
                    DocxMimeType => CreateDocumentContentBlock(DocumentFormat.Docx, bytes),
                    PdfMimeType => CreateDocumentContentBlock(DocumentFormat.Pdf, bytes),
                    XlsMimeType => CreateDocumentContentBlock(DocumentFormat.Xls, bytes),
                    XlsxMimeType => CreateDocumentContentBlock(DocumentFormat.Xlsx, bytes),
                    MpegMimeType => CreateVideoContentBlock(VideoFormat.Mpeg, bytes),
                    Mp4MimeType => CreateVideoContentBlock(VideoFormat.Mp4, bytes),
                    WebmMimeType => CreateVideoContentBlock(VideoFormat.Webm, bytes),
                    ThreeGpMimeType => CreateVideoContentBlock(VideoFormat.Three_gp, bytes),
                    MovMimeType => CreateVideoContentBlock(VideoFormat.Mov, bytes),
                    _ => throw new InvalidOperationException($"Unsupported image format: '{match.Groups["type"].Value}'"),
                };
            }
            else
            {
                yield return new ToolResultContentBlock { Text = text };
            }
        }
        else if (result is Exception e)
        {
            yield return new ToolResultContentBlock { Text = e.Message };
            yield return new ToolResultContentBlock { Text = e.StackTrace };
        }
        else
        {
            yield return new ToolResultContentBlock
            {
                Text = JsonSerializer.Serialize(result)
            };
        }
    }

    private static IEnumerable<ContentBlock> MessageContentItemsToContentBlock(ChatMessageContentItemCollection items)
    {
        return items.Where(IsContentSupported)
            .Select((item, i) =>
            {
                if (item is TextContent text)
                {
                    return new ContentBlock { Text = text.Text };
                }
                if (item is FunctionCallContent functionCall)
                {
                    return new ContentBlock
                    {
                        ToolUse = new ToolUseBlock
                        {
                            Name = FunctionName.ToFullyQualifiedName(functionCall.FunctionName, functionCall.PluginName),
                            Input = Document.FromObject(functionCall.Arguments),
                            ToolUseId = functionCall.Id,
                        }
                    };
                }
                if (item is FunctionResultContent functionResult)
                {
                    return new ContentBlock
                    {
                        ToolResult = new ToolResultBlock
                        {
                            ToolUseId = functionResult.CallId,
                            Content = ConvertResultToToolResultContentBlocks(functionResult.Result).ToList(),
                            Status = functionResult.Result is Exception ? ToolResultStatus.Error : ToolResultStatus.Success,
                        }
                    };
                }
                if (item is ImageContent image)
                {
                    Debug.Assert(image.DataUri != null);
                    return new ContentBlock
                    {
                        Image = new ImageBlock
                        {
                            Format = MimeTypeToImageFormat(image.MimeType),
                            Source = new ImageSource
                            {
                                Bytes = new MemoryStream(image.Data?.ToArray() ?? [])
                            }
                        }
                    };
                }
                if (item is PdfContent pdf)
                {
                    Debug.Assert(pdf.DataUri != null);
                    return new ContentBlock
                    {
                        Document = new DocumentBlock
                        {
                            Format = DocumentFormat.Pdf,
                            Name = $"document-{i + 1}",
                            Source = new DocumentSource
                            {
                                Bytes = new MemoryStream(pdf.Data?.ToArray() ?? [])
                            }
                        }
                    };
                }
                if (item is DocContent doc)
                {
                    Debug.Assert(doc.DataUri != null);
                    return new ContentBlock
                    {
                        Document = new DocumentBlock
                        {
                            Format = DocumentFormat.Doc,
                            Name = $"document-{i + 1}",
                            Source = new DocumentSource
                            {
                                Bytes = new MemoryStream(doc.Data?.ToArray() ?? [])
                            }
                        }
                    };
                }
                if (item is DocxContent docx)
                {
                    Debug.Assert(docx.DataUri != null);
                    return new ContentBlock
                    {
                        Document = new DocumentBlock
                        {
                            Format = DocumentFormat.Docx,
                            Name = $"document-{i + 1}",
                            Source = new DocumentSource
                            {
                                Bytes = new MemoryStream(docx.Data?.ToArray() ?? [])
                            }
                        }
                    };
                }
                return null;
            })
            .Where(item => item != null)
            .Select(item => item!)
            // For some reason, tool results have to be the first content blocks in the message
            .OrderBy(item => item.ToolResult != null ? 1 : !string.IsNullOrWhiteSpace(item.Text) ? 2 : 3);
    }

    private static bool IsContentEmpty(ChatMessageContent message)
    {
        return string.IsNullOrWhiteSpace(message.Content) && message.Items.Count == 0;
    }

    /// <summary>
    /// Creates the list of user and assistant messages for the Converse Request from the Chat History.
    /// </summary>
    /// <param name="chatHistory">The ChatHistory object to be building the message list from.</param>
    /// <returns>The list of messages for the converse request.</returns>
    /// <exception cref="ArgumentException">Thrown if invalid last message in chat history.</exception>
    internal static List<Message> BuildMessageList(ChatHistory chatHistory)
    {
        // Check that the text from the latest message in the chat history  is not empty.
        // Check that the text from the latest message in the chat history  is not empty.
        Verify.NotNullOrEmpty(chatHistory);
        return IsContentEmpty(chatHistory[^1])
            ? throw new ArgumentException("Last message in chat history was empty.")
            : [.. chatHistory
            .Where(m => m.Role != AuthorRole.System)
            .Select(m => new Message
            {
                Role = MapAuthorRoleToConversationRole(m.Role, m.Items.Any(i => i is FunctionResultContent)),
                Content = MessageContentItemsToContentBlock(m.Items).ToList()
            })];
    }

    /// <summary>
    /// Gets the prompt execution settings extension data for the model request body build.
    /// Returns null if the extension data value is not set (default is null if TValue is a nullable type).
    /// </summary>
    /// <param name="extensionData">The execution settings extension data.</param>
    /// <param name="key">The key name of the settings parameter</param>
    /// <typeparam name="TValue">The value of the settings parameter</typeparam>
    /// <returns>The conversion to the given value of the data for execution settings</returns>
    internal static TValue? GetExtensionDataValue<TValue>(IDictionary<string, object>? extensionData, string key)
    {
        if (extensionData?.TryGetValue(key, out object? value) == true)
        {
            try
            {
                return (TValue)value;
            }
            catch (InvalidCastException)
            {
                // Handle the case where the value cannot be cast to TValue
                return default;
            }
        }

        // As long as TValue is nullable this will be properly set to null
        return default;
    }

    /// <summary>
    /// Sets Prompt Execution Settings data if the value is not null.
    /// </summary>
    /// <param name="getValue">Getter function delegate</param>
    /// <param name="setValue">Setter function delegate</param>
    /// <typeparam name="T">Parameter type</typeparam>
    internal static void SetPropertyIfNotNull<T>(Func<T?> getValue, Action<T> setValue) where T : struct
    {
        var value = getValue();
        if (value.HasValue)
        {
            setValue(value.Value);
        }
    }

    /// <summary>
    /// Sets nullable property if the value is not null.
    /// </summary>
    /// <param name="getValue">Getter function delegate</param>
    /// <param name="setValue">Setter function delegate</param>
    /// <typeparam name="T">Parameter type</typeparam>
    internal static void SetNullablePropertyIfNotNull<T>(Func<T?> getValue, Action<T?> setValue) where T : class
    {
        var value = getValue();
        setValue(value);
    }

    [GeneratedRegex("data:(?<type>.+?);base64,(?<data>.+)")]
    private static partial Regex DataUriRegex();
}
