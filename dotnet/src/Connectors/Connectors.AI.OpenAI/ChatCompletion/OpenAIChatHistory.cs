// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.AI.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;

/// <summary>
/// OpenAI Chat content
/// See https://platform.openai.com/docs/guides/chat for details
/// </summary>
public class OpenAIChatHistory : ChatHistory
{
    /// <summary>
    /// Create a new and empty chat history
    /// </summary>
    /// <param name="assistantInstructions">Optional instructions for the assistant</param>
    public OpenAIChatHistory(string? assistantInstructions = null)
    {
        if (!string.IsNullOrWhiteSpace(assistantInstructions))
        {
            this.AddSystemMessage(assistantInstructions!);
        }
    }
}
