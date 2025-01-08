// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using Azure.AI.Projects;

namespace Microsoft.SemanticKernel.Agents.AzureAI.Internal;

/// <summary>
/// Factory for creating <see cref="MessageContent"/> based on <see cref="ChatMessageContent"/>.
/// </summary>
/// <remarks>
/// Improves testability.
/// </remarks>
internal static class AgentMessageFactory
{
    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="message">The message content.</param>
    public static Dictionary<string, string> GetMetadata(ChatMessageContent message)
    {
        return message.Metadata?.ToDictionary(kvp => kvp.Key, kvp => kvp.Value?.ToString() ?? string.Empty) ?? [];
    }

    ///// <summary>
    ///// Translates <see cref="ChatMessageContent.Items"/> into enumeration of <see cref="MessageContent"/>.
    ///// </summary>
    ///// <param name="message">The message content.</param>
    //public static IEnumerable<MessageContent> GetMessageContents(ChatMessageContent message) // %%%
    //{
    //    bool hasTextContent = message.Items.OfType<TextContent>().Any();
    //    foreach (KernelContent content in message.Items)
    //    {
    //        if (content is TextContent textContent)
    //        {
    //            yield return new MessageTextContent(content.ToString());
    //        }
    //        else if (content is ImageContent imageContent)
    //        {
    //            if (imageContent.Uri != null)
    //            {
    //                yield return MessageContent.FromImageUri(imageContent.Uri);
    //            }
    //            else if (!string.IsNullOrWhiteSpace(imageContent.DataUri))
    //            {
    //                yield return MessageContent.FromImageUri(new(imageContent.DataUri!));
    //            }
    //        }
    //        else if (content is FileReferenceContent fileContent)
    //        {
    //            yield return MessageContent.FromImageFileId(fileContent.FileId);
    //        }
    //        else if (content is FunctionResultContent resultContent && resultContent.Result != null && !hasTextContent)
    //        {
    //            // Only convert a function result when text-content is not already present
    //            yield return MessageContent.FromText(FunctionCallsProcessor.ProcessFunctionResult(resultContent.Result));
    //        }
    //    }
    //}

    internal static IEnumerable<ThreadMessageOptions> GetThreadMessages(IReadOnlyList<ChatMessageContent>? messages)
    {
        //if (options?.Messages is not null)
        //{
        //    foreach (ChatMessageContent message in options.Messages)
        //    {
        //        AzureAIP.ThreadMessageOptions threadMessage = new(
        //            role: message.Role == AuthorRole.User ? AzureAIP.MessageRole.User : AzureAIP.MessageRole.Agent,
        //            content: AgentMessageFactory.GetMessageContents(message));

        //        createOptions.InitialMessages.Add(threadMessage);
        //    }
        //}

        throw new NotImplementedException();
    }
}
