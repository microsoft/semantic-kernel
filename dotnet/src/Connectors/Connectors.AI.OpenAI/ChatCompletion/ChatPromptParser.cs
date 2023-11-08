// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Prompt;
using System;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;

internal static class ChatPromptParser
{
    private const string MessageTagName = "message";
    private const string RoleAttributeName = "role";

    public static bool TryParse(List<PromptNode> nodes, out ChatHistory chatHistory)
    {
        chatHistory = new ChatHistory();

        foreach (var node in nodes)
        {
            if (IsValidChatMessage(node))
            {
                var role = node.Attributes[RoleAttributeName];
                var content = node.Content!;

                chatHistory.AddMessage(new AuthorRole(role), content);
            }
        }

        return chatHistory.Count != 0;
    }

    private static bool IsValidChatMessage(PromptNode node)
    {
        return
            node.TagName.Equals(MessageTagName, StringComparison.OrdinalIgnoreCase) &&
            node.Attributes.ContainsKey(RoleAttributeName) &&
            node.Content is not null;
    }
}
