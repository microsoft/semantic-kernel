// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json;
using Anthropic.Models.Messages;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.Anthropic.Core;

/// <summary>
/// Partial class containing message and content converters.
/// </summary>
internal partial class AnthropicClientCore
{
    #region Message Converters

    /// <summary>
    /// Converts chat history to Anthropic messages with tool message grouping.
    /// </summary>
    /// <remarks>
    /// Anthropic requires that parallel tool result messages are grouped together in a single
    /// user message. When the model requests multiple tool calls in parallel, all corresponding
    /// tool results must be sent back in a single message with multiple tool_result content blocks.
    ///
    /// This method implements the same grouping logic as the Python SK Anthropic connector:
    /// - If a Tool message follows an Assistant message → create a new user message
    /// - If a Tool message follows another Tool message → append to the previous message
    /// </remarks>
    internal static List<MessageParam> ConvertChatHistoryToAnthropicMessages(ChatHistory chatHistory)
    {
        var messages = new List<MessageParam>();
        // Track content blocks separately to allow appending for tool message grouping
        var contentBlocksList = new List<List<ContentBlockParam>>();
        AuthorRole? previousRole = null;

        foreach (var message in chatHistory)
        {
            // Skip system messages - they are handled separately
            if (message.Role == AuthorRole.System)
            {
                continue;
            }

            // Check if this is a Tool message that should be grouped with the previous one
            if (message.Role == AuthorRole.Tool && previousRole == AuthorRole.Tool && messages.Count > 0)
            {
                // Append tool results to the previous message's content blocks
                var additionalBlocks = GetToolResultBlocks(message);
                var previousContentBlocks = contentBlocksList[^1];
                previousContentBlocks.AddRange(additionalBlocks);

                // Replace the previous message with updated content
                messages[^1] = new MessageParam
                {
                    Role = messages[^1].Role,
                    Content = previousContentBlocks
                };
            }
            else
            {
                // Convert and add as a new message
                var contentBlocks = ConvertToContentBlocks(message);
                contentBlocksList.Add(contentBlocks);

                var role = message.Role == AuthorRole.Assistant ? Role.Assistant : Role.User;
                messages.Add(new MessageParam
                {
                    Role = role,
                    Content = contentBlocks
                });
            }

            previousRole = message.Role;
        }

        return messages;
    }

    #endregion

    #region Content Block Converters

    /// <summary>
    /// Converts a ChatMessageContent to a list of Anthropic ContentBlockParam.
    /// </summary>
    /// <param name="message">The chat message content to convert.</param>
    /// <returns>A list of content block parameters.</returns>
    /// <exception cref="ArgumentException">Thrown when the message has no valid content blocks.</exception>
    private static List<ContentBlockParam> ConvertToContentBlocks(ChatMessageContent message)
    {
        var contentBlocks = new List<ContentBlockParam>();

        foreach (var item in message.Items)
        {
            switch (item)
            {
                case TextContent textContent:
                    // Skip TextContent for Tool messages - Claude requires only tool_result blocks
                    // after tool_use. Including text blocks causes API error:
                    // "tool_use ids were found without tool_result blocks immediately after"
                    if (message.Role == AuthorRole.Tool)
                    {
                        break;
                    }
                    if (!string.IsNullOrWhiteSpace(textContent.Text))
                    {
                        contentBlocks.Add(new TextBlockParam { Text = textContent.Text! });
                    }
                    break;

                case ImageContent imageContent:
                    var imageBlock = ConvertImageContent(imageContent);
                    if (imageBlock != null)
                    {
                        contentBlocks.Add(imageBlock);
                    }
                    break;

                case FunctionCallContent functionCall:
                    contentBlocks.Add(ConvertFunctionCallContent(functionCall));
                    break;

                case FunctionResultContent functionResult:
                    contentBlocks.Add(ConvertFunctionResultContent(functionResult));
                    break;
            }
        }

        // If no content blocks, add text content from message (if non-empty)
        if (contentBlocks.Count == 0 && !string.IsNullOrWhiteSpace(message.Content))
        {
            contentBlocks.Add(new TextBlockParam { Text = message.Content! });
        }

        // Anthropic requires at least one content block per message
        if (contentBlocks.Count == 0)
        {
            throw new ArgumentException(
                "Cannot convert message to Anthropic format: no valid content blocks. " +
                "Message must contain at least one non-empty text, image, or function content.",
                nameof(message));
        }

        return contentBlocks;
    }

    /// <summary>
    /// Extracts tool result content blocks from a message.
    /// </summary>
    private static List<ContentBlockParam> GetToolResultBlocks(ChatMessageContent message)
    {
        var blocks = new List<ContentBlockParam>();
        foreach (var item in message.Items)
        {
            if (item is FunctionResultContent functionResult)
            {
                blocks.Add(ConvertFunctionResultContent(functionResult));
            }
        }
        return blocks;
    }

    /// <summary>
    /// Converts FunctionCallContent to Anthropic ToolUseBlockParam.
    /// </summary>
    /// <exception cref="ArgumentException">Thrown when Id is null or empty.</exception>
    private static ToolUseBlockParam ConvertFunctionCallContent(FunctionCallContent functionCall)
    {
        // The ID must match the tool_use.id from the model's response.
        // When we receive a tool_use from the API and later send the result back,
        // both must have matching IDs for proper correlation.
        if (string.IsNullOrEmpty(functionCall.Id))
        {
            throw new ArgumentException(
                $"FunctionCallContent.Id is required for function '{functionCall.FunctionName}'. " +
                "The Id must be the tool_use ID from the model's response for proper result correlation.",
                nameof(functionCall));
        }

        var inputDict = functionCall.Arguments?.ToDictionary(
            kvp => kvp.Key,
            kvp => kvp.Value is JsonElement je ? je : JsonSerializer.SerializeToElement(kvp.Value))
            ?? new Dictionary<string, JsonElement>();

        return new ToolUseBlockParam
        {
            ID = functionCall.Id!,
            Name = functionCall.FunctionName,
            Input = inputDict
        };
    }

    /// <summary>
    /// Converts FunctionResultContent to Anthropic ToolResultBlockParam.
    /// </summary>
    /// <exception cref="ArgumentException">Thrown when CallId is null or empty.</exception>
    private static ToolResultBlockParam ConvertFunctionResultContent(FunctionResultContent functionResult)
    {
        if (string.IsNullOrEmpty(functionResult.CallId))
        {
            throw new ArgumentException(
                $"FunctionResultContent.CallId is required for function '{functionResult.FunctionName}'. " +
                "The CallId must match the tool_use ID from the model's response.",
                nameof(functionResult));
        }

        // Check for ImageContent (multimodal tool result).
        // Note: Currently FunctionCallsProcessor converts all results to strings, so this check
        // will not match. This is forward-compatible preparation for when FunctionCallsProcessor
        // is updated to preserve ImageContent objects (see: https://github.com/microsoft/semantic-kernel/issues/XXXXX).
        // Anthropic API natively supports images in tool results via ToolResultBlockParam.Content.
        if (functionResult.Result is ImageContent imageContent)
        {
            return ConvertImageResultContent(functionResult.CallId!, imageContent);
        }

        var resultString = functionResult.Result?.ToString() ?? string.Empty;

        // Detect errors to set IsError flag for the Anthropic API.
        // Two error scenarios are handled:
        // 1. Manual function invocation: Users may pass Exception objects directly to FunctionResultContent
        // 2. Auto function invocation: FunctionCallsProcessor returns string error messages prefixed with "Error:"
        var isError = functionResult.Result is Exception ||
                      (functionResult.Result is string && resultString.StartsWith("Error:", StringComparison.Ordinal));

        return new ToolResultBlockParam
        {
            // CallId is validated above - null/empty throws ArgumentException
            ToolUseID = functionResult.CallId!,
            Content = resultString,
            IsError = isError
        };
    }

    /// <summary>
    /// Converts ImageContent tool result to Anthropic ToolResultBlockParam with multimodal content.
    /// </summary>
    /// <remarks>
    /// The Anthropic API supports multimodal tool results via ToolResultBlockParam.Content as an array of content blocks.
    /// SDK Type Chain: ToolResultBlockParam.Content → ToolResultBlockParamContent (union type) → IReadOnlyList&lt;Block&gt;
    /// → Block (union type) → ImageBlockParam → ImageBlockParamSource (union type) → Base64ImageSource.
    /// All conversions are implicit (verified against official Anthropic NuGet package).
    /// </remarks>
    private static ToolResultBlockParam ConvertImageResultContent(string callId, ImageContent imageContent)
    {
        // ImageContent.Data is ReadOnlyMemory<byte>?
        if (!imageContent.Data.HasValue || imageContent.Data.Value.Length == 0)
        {
            // No binary data - return error (URI-only ImageContent not supported in tool results)
            return new ToolResultBlockParam
            {
                ToolUseID = callId,
                Content = "Error: ImageContent requires binary data (Data property). URI-only ImageContent is not supported in tool results.",
                IsError = true
            };
        }

        var imageData = imageContent.Data.Value;
        var base64Data = Convert.ToBase64String(imageData.ToArray());
        var mediaType = GetMediaType(imageContent.MimeType);

        // ToolResultBlockParam.Content accepts ToolResultBlockParamContent which can be:
        // - string (via implicit conversion)
        // - IReadOnlyList<Block> (via implicit conversion)
        // Block can contain ImageBlockParam (via implicit conversion)
        // ImageBlockParam.Source accepts ImageBlockParamSource which wraps Base64ImageSource (via implicit conversion)
        return new ToolResultBlockParam
        {
            ToolUseID = callId,
            Content = new List<Block>
            {
                new ImageBlockParam
                {
                    Source = new Base64ImageSource
                    {
                        Data = base64Data,
                        MediaType = mediaType
                    }
                }
            },
            IsError = false
        };
    }

    /// <summary>
    /// Converts ImageContent to Anthropic ImageBlockParam.
    /// </summary>
    private static ImageBlockParam? ConvertImageContent(ImageContent imageContent)
    {
        // Handle base64 data
        if (imageContent.Data != null && imageContent.Data.Value.Length > 0)
        {
            var base64Data = Convert.ToBase64String(imageContent.Data.Value.ToArray());
            var mediaType = GetMediaType(imageContent.MimeType);

            return new ImageBlockParam
            {
                Source = new Base64ImageSource
                {
                    Data = base64Data,
                    MediaType = mediaType
                }
            };
        }

        // Handle URL
        if (imageContent.Uri != null)
        {
            return new ImageBlockParam
            {
                Source = new URLImageSource
                {
                    URL = imageContent.Uri.ToString()
                }
            };
        }

        return null;
    }

    /// <summary>
    /// Gets the Anthropic media type from MIME type string.
    /// </summary>
    /// <param name="mimeType">The MIME type string (e.g., "image/png").</param>
    /// <returns>The corresponding Anthropic MediaType.</returns>
    /// <remarks>
    /// Anthropic API supports: image/jpeg, image/png, image/gif, image/webp.
    /// For unrecognized or missing MIME types, defaults to JPEG.
    /// </remarks>
    private static MediaType GetMediaType(string? mimeType)
    {
        var upperMimeType = mimeType?.ToUpperInvariant();
        return upperMimeType switch
        {
            "IMAGE/PNG" => MediaType.ImagePNG,
            "IMAGE/GIF" => MediaType.ImageGIF,
            "IMAGE/WEBP" => MediaType.ImageWebP,
            "IMAGE/JPEG" => MediaType.ImageJPEG,
            _ => MediaType.ImageJPEG // Unrecognized or missing MIME type
        };
    }

    #endregion

    #region Response Converters

    /// <summary>
    /// Converts Anthropic Message response to ChatMessageContent list.
    /// </summary>
    private static IReadOnlyList<ChatMessageContent> ConvertResponseToChatMessageContents(Message response)
    {
        var textParts = new StringBuilder();
        var functionCallContents = new List<FunctionCallContent>();

        foreach (var block in response.Content)
        {
            if (block.TryPickText(out var textBlock))
            {
                textParts.Append(textBlock.Text);
            }
            else if (block.TryPickToolUse(out var toolUse))
            {
                // toolUse.Input is IReadOnlyDictionary<string, JsonElement>
                var kernelArgs = ConvertToolInputToKernelArguments(toolUse.Input);

                // Parse the fully-qualified name to extract plugin and function names
                var parsedName = FunctionName.Parse(toolUse.Name, AnthropicFunctionNameSeparator);
                functionCallContents.Add(new FunctionCallContent(
                    functionName: parsedName.Name,
                    pluginName: parsedName.PluginName,
                    id: toolUse.ID,
                    arguments: kernelArgs));
            }
        }

        var metadata = new Dictionary<string, object?>
        {
            ["Id"] = response.ID,
            ["StopReason"] = response.StopReason?.Value().ToString(),
            ["FinishReason"] = MapStopReasonToFinishReason(response.StopReason),
            ["InputTokens"] = response.Usage?.InputTokens,
            ["OutputTokens"] = response.Usage?.OutputTokens
        };

        var chatMessage = new ChatMessageContent(
            AuthorRole.Assistant,
            textParts.Length > 0 ? textParts.ToString() : string.Empty,
            response.Model,
            innerContent: response,
            encoding: Encoding.UTF8,
            metadata: metadata);

        // Add function calls to the message
        foreach (var fc in functionCallContents)
        {
            chatMessage.Items.Add(fc);
        }

        return [chatMessage];
    }

    /// <summary>
    /// Converts Anthropic tool input (IReadOnlyDictionary with JsonElement values) to KernelArguments.
    /// </summary>
    internal static KernelArguments ConvertToolInputToKernelArguments(IReadOnlyDictionary<string, JsonElement>? input)
    {
        var kernelArgs = new KernelArguments();
        if (input == null)
        {
            return kernelArgs;
        }

        foreach (var kvp in input)
        {
            // Convert JsonElement to appropriate .NET type
            kernelArgs[kvp.Key] = ConvertJsonElementToObject(kvp.Value);
        }
        return kernelArgs;
    }

    /// <summary>
    /// Converts a JsonElement to an appropriate .NET object.
    /// </summary>
    internal static object? ConvertJsonElementToObject(JsonElement element)
    {
        return element.ValueKind switch
        {
            JsonValueKind.String => element.GetString(),
            JsonValueKind.Number => element.TryGetInt64(out var l) ? l : element.GetDouble(),
            JsonValueKind.True => true,
            JsonValueKind.False => false,
            JsonValueKind.Null => null,
            JsonValueKind.Array => element.EnumerateArray().Select(ConvertJsonElementToObject).ToArray(),
            JsonValueKind.Object => element.EnumerateObject().ToDictionary(p => p.Name, p => ConvertJsonElementToObject(p.Value)),
            _ => element.GetRawText()
        };
    }

    /// <summary>
    /// Parses tool arguments from JSON string.
    /// </summary>
    /// <exception cref="ArgumentException">Thrown when JSON parsing fails.</exception>
    private static Dictionary<string, object?> ParseToolArguments(string json)
    {
        if (string.IsNullOrWhiteSpace(json))
        {
            return new Dictionary<string, object?>();
        }

        try
        {
            var result = JsonSerializer.Deserialize<Dictionary<string, object?>>(json);
            return result ?? new Dictionary<string, object?>();
        }
        catch (JsonException ex)
        {
            throw new ArgumentException(
                $"Failed to parse tool arguments JSON. The model returned malformed JSON: {json}",
                nameof(json),
                ex);
        }
    }

    /// <summary>
    /// Converts a dictionary to KernelArguments.
    /// </summary>
    private static KernelArguments ConvertToKernelArguments(IDictionary<string, object?> arguments)
    {
        var kernelArgs = new KernelArguments();
        foreach (var kvp in arguments)
        {
            kernelArgs[kvp.Key] = kvp.Value;
        }
        return kernelArgs;
    }

    /// <summary>
    /// Builds the input schema for a kernel function.
    /// </summary>
    private static InputSchema BuildInputSchema(KernelFunctionMetadata function)
    {
        var properties = new Dictionary<string, JsonElement>();
        var required = new List<string>();

        foreach (var param in function.Parameters)
        {
            var propSchema = new Dictionary<string, object>
            {
                ["type"] = GetJsonSchemaType(param.ParameterType)
            };

            if (!string.IsNullOrEmpty(param.Description))
            {
                propSchema["description"] = param.Description;
            }

            properties[param.Name] = JsonSerializer.SerializeToElement(propSchema);

            if (param.IsRequired)
            {
                required.Add(param.Name);
            }
        }

        return new InputSchema
        {
            Properties = properties,
            Required = required.Count > 0 ? required : null
        };
    }

    /// <summary>
    /// Gets the JSON schema type for a .NET type.
    /// </summary>
    internal static string GetJsonSchemaType(System.Type? type)
    {
        if (type == null)
        {
            return "string";
        }

        var underlyingType = Nullable.GetUnderlyingType(type) ?? type;

        return underlyingType switch
        {
            System.Type t when t == typeof(bool) => "boolean",
            System.Type t when t == typeof(int) || t == typeof(long) || t == typeof(short) || t == typeof(byte) => "integer",
            System.Type t when t == typeof(float) || t == typeof(double) || t == typeof(decimal) => "number",
            System.Type t when t.IsArray || typeof(System.Collections.IEnumerable).IsAssignableFrom(t) && t != typeof(string) => "array",
            System.Type t when t.IsClass && t != typeof(string) => "object",
            _ => "string"
        };
    }

    /// <summary>
    /// Maps Anthropic stop reasons to Semantic Kernel finish reasons.
    /// </summary>
    /// <remarks>
    /// Anthropic stop reasons:
    /// - "end_turn": Natural end of the model's turn → "stop"
    /// - "max_tokens": Maximum token limit reached → "length"
    /// - "tool_use": Model wants to use a tool → "tool_calls"
    /// - "stop_sequence": A stop sequence was generated → "stop"
    ///
    /// This mapping aligns with the Python SK Anthropic connector's ANTHROPIC_TO_SEMANTIC_KERNEL_FINISH_REASON_MAP.
    /// </remarks>
    internal static string? MapStopReasonToFinishReason(global::Anthropic.Core.ApiEnum<string, StopReason>? stopReasonEnum)
    {
        if (stopReasonEnum is not { } nonNullStopReason)
        {
            return null;
        }

        // Get the raw string value from the ApiEnum
        var rawValue = nonNullStopReason.Raw();

        // CA1308: ToLowerInvariant is intentional here - finish reasons are conventionally lowercase
        // (e.g., "stop", "length", "tool_calls") to match OpenAI and other providers.
#pragma warning disable CA1308
        return rawValue switch
        {
            "end_turn" => "stop",
            "max_tokens" => "length",
            "tool_use" => "tool_calls",
            "stop_sequence" => "stop",
            _ => rawValue?.ToLowerInvariant()
        };
#pragma warning restore CA1308
    }

    #endregion
}
