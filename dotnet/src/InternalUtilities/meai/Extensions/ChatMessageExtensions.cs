// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.Extensions.AI;

[ExcludeFromCodeCoverage]
internal static class ChatMessageExtensions
{
    /// <summary>Converts a <see cref="ChatMessage"/> to a <see cref="ChatMessageContent"/>.</summary>
    internal static ChatMessageContent ToChatMessageContent(this ChatMessage message, Microsoft.Extensions.AI.ChatResponse? response = null)
    {
        ChatMessageContent result = new()
        {
            ModelId = response?.ModelId,
            AuthorName = message.AuthorName,
            InnerContent = response?.RawRepresentation ?? message.RawRepresentation,
            Metadata = new AdditionalPropertiesDictionary(message.AdditionalProperties ?? []) { ["Usage"] = response?.Usage },
            Role = new AuthorRole(message.Role.Value),
        };

        foreach (AIContent content in message.Contents)
        {
#pragma warning disable SKEXP0001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
            KernelContent? resultContent = content switch
            {
                Microsoft.Extensions.AI.TextContent tc => new Microsoft.SemanticKernel.TextContent(tc.Text),
                Microsoft.Extensions.AI.DataContent dc when dc.HasTopLevelMediaType("image") => new Microsoft.SemanticKernel.ImageContent(dc.Uri),
                Microsoft.Extensions.AI.UriContent uc when uc.HasTopLevelMediaType("image") => new Microsoft.SemanticKernel.ImageContent(uc.Uri),
                Microsoft.Extensions.AI.DataContent dc when dc.HasTopLevelMediaType("audio") => new Microsoft.SemanticKernel.AudioContent(dc.Uri),
                Microsoft.Extensions.AI.UriContent uc when uc.HasTopLevelMediaType("audio") => new Microsoft.SemanticKernel.AudioContent(uc.Uri),
                Microsoft.Extensions.AI.DataContent dc => new Microsoft.SemanticKernel.BinaryContent(dc.Uri),
                Microsoft.Extensions.AI.UriContent uc => new Microsoft.SemanticKernel.BinaryContent(uc.Uri),
                Microsoft.Extensions.AI.FunctionCallContent fcc => CreateFunctionCallContent(fcc),
                Microsoft.Extensions.AI.FunctionResultContent frc => CreateFunctionResultContent(frc),
                _ => null
            };
#pragma warning restore SKEXP0001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

            if (resultContent is not null)
            {
                resultContent.Metadata = content.AdditionalProperties;
                resultContent.InnerContent = content.RawRepresentation;
                resultContent.ModelId = response?.ModelId;
                result.Items.Add(resultContent);
            }
        }

        return result;

        Microsoft.SemanticKernel.FunctionCallContent CreateFunctionCallContent(Microsoft.Extensions.AI.FunctionCallContent functionCallContent)
        {
            var (functionName, pluginName) = ParseFunctionName(functionCallContent.Name);

            return new Microsoft.SemanticKernel.FunctionCallContent(
                functionName: functionName,
                pluginName: pluginName,
                id: functionCallContent.CallId,
                arguments: functionCallContent.Arguments is not null ? new(functionCallContent.Arguments) : null);
        }

        Microsoft.SemanticKernel.FunctionResultContent CreateFunctionResultContent(Microsoft.Extensions.AI.FunctionResultContent functionResultContent)
        {
            string? functionName = null;
            string? pluginName = null;

            if (GetFunctionCallContent(functionResultContent.CallId) is { } functionCallContent)
            {
                (functionName, pluginName) = ParseFunctionName(functionCallContent.Name);
            }

            return new Microsoft.SemanticKernel.FunctionResultContent(
                functionName: functionName,
                pluginName: pluginName,
                callId: functionResultContent.CallId,
                result: functionResultContent.Result);
        }

        static (string FunctionName, string? PluginName) ParseFunctionName(string? name)
        {
            if (string.IsNullOrWhiteSpace(name))
            {
                return (string.Empty, null);
            }

            // Most connectors use "." or "-" as the fully-qualified separator.
            var parsed = FunctionName.Parse(name, ".");
            if (!string.IsNullOrEmpty(parsed.PluginName))
            {
                return (parsed.Name, parsed.PluginName);
            }

            parsed = FunctionName.Parse(name, "-");
            if (!string.IsNullOrEmpty(parsed.PluginName))
            {
                return (parsed.Name, parsed.PluginName);
            }

            // Some Ollama models return tool names as "<plugin>_<FunctionName>".
            int underscore = name.IndexOf('_');
            if (underscore > 0 &&
                underscore == name.LastIndexOf('_') &&
                underscore + 1 < name.Length &&
                char.IsUpper(name[underscore + 1]))
            {
                parsed = FunctionName.Parse(name, "_");
                if (!string.IsNullOrEmpty(parsed.PluginName))
                {
                    return (parsed.Name, parsed.PluginName);
                }
            }

            return (name, null);
        }

        Microsoft.Extensions.AI.FunctionCallContent? GetFunctionCallContent(string callId)
            => response?.Messages
                .Select(m => m.Contents
                .FirstOrDefault(c => c is Microsoft.Extensions.AI.FunctionCallContent fcc && fcc.CallId == callId) as Microsoft.Extensions.AI.FunctionCallContent)
                    .FirstOrDefault(fcc => fcc is not null);
    }

    /// <summary>Converts a list of <see cref="ChatMessage"/> to a <see cref="ChatHistory"/>.</summary>
    internal static ChatHistory ToChatHistory(this IEnumerable<ChatMessage> chatMessages)
    {
        ChatHistory chatHistory = [];
        foreach (var message in chatMessages)
        {
            chatHistory.Add(message.ToChatMessageContent());
        }
        return chatHistory;
    }
}
