// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Step04.Steps;

/// <summary>
/// %%%
/// </summary>
public class RenderMessageStep : KernelProcessStep
{
    public static class Functions
    {
        public const string RenderError = nameof(RenderMessageStep.RenderError);
        public const string RenderMessage = nameof(RenderMessageStep.RenderMessage);
        public const string RenderMessages = nameof(RenderMessageStep.RenderMessages);
        public const string RenderUserText = nameof(RenderMessageStep.RenderUserText);
    }

    [KernelFunction]
    public void RenderError(string message)
    {
        Console.WriteLine($"ERROR: {message}");
    }

    [KernelFunction]
    public void RenderUserText(string message)
    {
        Console.WriteLine($"{AuthorRole.User.Label.ToUpperInvariant()}: {message}");
    }

    [KernelFunction]
    public void RenderMessage(ChatMessageContent message)
    {
        Render(message);
    }

    [KernelFunction]
    public void RenderMessages(IEnumerable<ChatMessageContent> messages)
    {
        foreach (ChatMessageContent message in messages)
        {
            Render(message);
        }
    }

    public static void Render(ChatMessageContent message)
    {
        string displayName = !string.IsNullOrWhiteSpace(message.AuthorName) ? $" - {message.AuthorName}" : string.Empty;
        Console.WriteLine($"{message.Role.Label.ToUpperInvariant()}{displayName}: {message.Content}");
    }
}
