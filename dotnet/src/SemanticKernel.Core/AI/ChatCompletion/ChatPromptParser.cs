// Copyright (c) Microsoft. All rights reserved.

using System.Text.RegularExpressions;

namespace Microsoft.SemanticKernel.AI.ChatCompletion;

/// <summary>
/// Parser for chat completion prompts.
/// </summary>
public static class ChatPromptParser
{
    /// <summary>
    /// Regex to fetch value from "role" attribute and content inside "message" tag.
    /// </summary>
    private static readonly Regex s_chatHistoryRegex = new(@"<message role=[""']([^""']+)[""']>\s*([^<]+?)\s*</message>");

    /// <summary>
    /// Tries to get instance of <see cref="ChatHistory"/> from given prompt.
    /// </summary>
    /// <param name="prompt">Prompt to parse.</param>
    /// <param name="chatHistory">Instance of <see cref="ChatHistory"/> if given prompt is chat prompt, otherwise null.</param>
    /// <returns>Boolean flag that indicates if given prompt is chat prompt or not.</returns>
    public static bool TryGetChatHistory(string prompt, out ChatHistory? chatHistory)
    {
        var matchCollection = s_chatHistoryRegex.Matches(prompt);

        if (matchCollection.Count == 0)
        {
            chatHistory = null;
            return false;
        }

        chatHistory = new ChatHistory();

        foreach (Match match in matchCollection)
        {
            string role = match.Groups[1].Value;
            string content = match.Groups[2].Value;

            chatHistory.AddMessage(new AuthorRole(role), content);
        }

        return true;
    }
}
