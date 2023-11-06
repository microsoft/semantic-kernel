// Copyright (c) Microsoft. All rights reserved.

using System.Text.RegularExpressions;
using static System.Net.Mime.MediaTypeNames;

namespace Microsoft.SemanticKernel.AI.ChatCompletion;

public static class ChatPromptParser
{
    private static readonly Regex s_chatHistoryRegex = new(@"<message role=[""']([^""']+)[""']>\s*([^<]+?)\s*</message>");

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
