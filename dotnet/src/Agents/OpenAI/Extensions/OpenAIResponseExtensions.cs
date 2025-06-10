// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Responses;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

internal static class OpenAIResponseExtensions
{
    /// <summary>
    /// Converts a <see cref="OpenAIResponse"/> instance to a <see cref="ChatMessageContent"/>.
    /// </summary>
    /// <param name="response">The response to convert.</param>
    /// <returns>A <see cref="ChatMessageContent"/> instance.</returns>
    public static ChatMessageContent ToChatMessageContent(this OpenAIResponse response)
    {
        var messageItem = response.OutputItems
            .FirstOrDefault(item => item is MessageResponseItem);
        var role = messageItem is MessageResponseItem messageResponseItem
            ? messageResponseItem.Role.ToAuthorRole()
            : AuthorRole.Assistant; // Default to Assistant if no role is specified

        var kernelContents = response.OutputItems
            .SelectMany(item => item.ToChatMessageContentItemCollection())
            .ToList();
        ChatMessageContentItemCollection items = new();
        items.AddRange(kernelContents);

        return new ChatMessageContent(
            role,
            modelId: response.Model,
            items: items,
            innerContent: response
            );
    }

    /// <summary>
    /// Converts a <see cref="ResponseItem"/> instance to a <see cref="ChatMessageContent"/>.
    /// </summary>
    /// <param name="item">The response item to convert.</param>
    /// <returns>A <see cref="ChatMessageContent"/> instance.</returns>
    public static ChatMessageContent ToChatMessageContent(this ResponseItem item)
    {
        if (item is MessageResponseItem messageResponseItem)
        {
            var role = messageResponseItem.Role.ToAuthorRole();
            return new ChatMessageContent(role, item.ToChatMessageContentItemCollection(), innerContent: messageResponseItem);
        }
        else if (item is FunctionCallResponseItem functionCallResponseItem)
        {
            return new ChatMessageContent(AuthorRole.Assistant, item.ToChatMessageContentItemCollection(), innerContent: functionCallResponseItem);
        }
        throw new NotSupportedException($"Unsupported response item: {item.GetType()}");
    }

    /// <summary>
    /// Converts a <see cref="ResponseItem"/> instance to a <see cref="ChatMessageContent"/>.
    /// </summary>
    /// <param name="item">The response item to convert.</param>
    /// <returns>A <see cref="ChatMessageContent"/> instance.</returns>
    public static ChatMessageContentItemCollection ToChatMessageContentItemCollection(this ResponseItem item)
    {
        if (item is MessageResponseItem messageResponseItem)
        {
            return messageResponseItem.Content.ToChatMessageContentItemCollection();
        }
        else if (item is FunctionCallResponseItem functionCallResponseItem)
        {
            Exception? exception = null;
            KernelArguments? arguments = null;
            try
            {
                arguments = JsonSerializer.Deserialize<KernelArguments>(functionCallResponseItem.FunctionArguments);
            }
            catch (JsonException ex)
            {
                exception = new KernelException("Error: Function call arguments were invalid JSON.", ex);
            }
            var functionName = FunctionName.Parse(functionCallResponseItem.FunctionName, "-");
            var functionCallContent = new FunctionCallContent(
                    functionName: functionName.Name,
                    pluginName: functionName.PluginName,
                    id: functionCallResponseItem.CallId,
                    arguments: arguments)
            {
                InnerContent = functionCallResponseItem,
                Exception = exception
            };
            return [functionCallContent];
        }
        throw new NotImplementedException($"Unsupported response item: {item.GetType()}");
    }

    /// <summary>
    /// Converts a <see cref="FunctionCallResponseItem"/> to a <see cref="FunctionCallContent"/>.
    /// </summary>
    /// <param name="functionCallResponseItem">The response item to convert.</param>
    /// <returns>A <see cref="FunctionCallContent"/> instance.</returns>
    public static FunctionCallContent ToFunctionCallContent(this FunctionCallResponseItem functionCallResponseItem)
    {
        Exception? exception = null;
        KernelArguments? arguments = null;
        try
        {
            arguments = JsonSerializer.Deserialize<KernelArguments>(functionCallResponseItem.FunctionArguments);
        }
        catch (JsonException ex)
        {
            exception = new KernelException("Error: Function call arguments were invalid JSON.", ex);
        }
        var functionName = FunctionName.Parse(functionCallResponseItem.FunctionName, "-");
        return new FunctionCallContent(
                functionName: functionName.Name,
                pluginName: functionName.PluginName,
                id: functionCallResponseItem.CallId,
                arguments: arguments)
        {
            InnerContent = functionCallResponseItem,
            Exception = exception
        };
    }

    /// <summary>
    /// Converts a <see cref="FunctionCallResponseItem"/> to a <see cref="FunctionCallContent"/>.
    /// </summary>
    /// <param name="functionCallResponseItem">The response item to convert.</param>
    /// <param name="functionArguments"></param>
    /// <returns>A <see cref="FunctionCallContent"/> instance.</returns>
    public static StreamingFunctionCallUpdateContent ToStreamingFunctionCallUpdateContent(this FunctionCallResponseItem functionCallResponseItem, string functionArguments)
    {
        return new StreamingFunctionCallUpdateContent(
                callId: functionCallResponseItem.CallId,
                name: functionCallResponseItem.FunctionName,
                arguments: functionArguments)
        {
            InnerContent = functionCallResponseItem,
        };
    }

    /// <summary>
    /// Converts a <see cref="MessageRole"/> to an <see cref="AuthorRole"/>.
    /// </summary>
    /// <param name="messageRole">The message role to convert.</param>
    /// <returns>An <see cref="AuthorRole"/> corresponding to the message role.</returns>
    public static AuthorRole ToAuthorRole(this MessageRole messageRole)
    {
        return messageRole switch
        {
            MessageRole.Assistant => AuthorRole.Assistant,
            MessageRole.Developer => AuthorRole.Developer,
            MessageRole.System => AuthorRole.System,
            MessageRole.User => AuthorRole.User,
            _ => new AuthorRole("unknown"),
        };
    }

    #region private
    private static ChatMessageContentItemCollection ToChatMessageContentItemCollection(this IList<ResponseContentPart> content)
    {
        var collection = new ChatMessageContentItemCollection();
        foreach (var part in content)
        {
            if (part.Kind == ResponseContentPartKind.OutputText || part.Kind == ResponseContentPartKind.InputText)
            {
                collection.Add(new TextContent(part.Text, innerContent: part));
            }
            else if (part.Kind == ResponseContentPartKind.InputImage)
            {
                collection.Add(new FileReferenceContent(part.InputImageFileId) { InnerContent = part });
            }
            else if (part.Kind == ResponseContentPartKind.InputFile)
            {
                collection.Add(new BinaryContent(part.InputFileBytes.ToArray(), part.InputFileBytes.MediaType) { InnerContent = part });
            }
            else if (part.Kind == ResponseContentPartKind.Refusal)
            {
                collection.Add(new TextContent(part.Refusal, innerContent: part));
            }
        }
        return collection;
    }
    #endregion

}
