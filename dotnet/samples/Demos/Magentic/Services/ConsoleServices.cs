// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
//using ChatTokenUsage = OpenAI.Chat.ChatTokenUsage;

namespace Magentic.Services;

internal sealed class ConsoleServices : IUXServices
{
    private int _totalTokens;
    private int _inputTokens;
    private int _outputTokens;

    /// <inheritdoc/>
    public ValueTask<string?> ReadInputAsync()
    {
        return ValueTask.FromResult(this.ReadInput());
    }

    public string? ReadInput(string label = "Input")
    {
        try
        {
            System.Console.ForegroundColor = ConsoleColor.Green;
            System.Console.Write($"\n{label}> ");
            System.Console.ForegroundColor = ConsoleColor.Yellow;
            return System.Console.ReadLine();
        }
        finally
        {
            System.Console.ResetColor();
        }
    }

    /// <inheritdoc/>
    public ValueTask DisplayChatAsync(ChatMessageContent message) => this.DisplayMessageAsync(message, ConsoleColor.Gray);

    /// <inheritdoc/>
    public ValueTask DisplayOutputAsync(ChatMessageContent message) => this.DisplayMessageAsync(message, ConsoleColor.White);

    ///// <inheritdoc/>
    //public ValueTask DisplayProgressAsync(ChatMessages.Progress message) // %%% TODO: Progress
    //{
    //    try
    //    {
    //        this.DisplayProgress(message.Label);
    //        if (message.TotalTokens != null &&
    //            message.InputTokens != null &&
    //            message.OutputTokens != null)
    //        {
    //            this.DisplayUsage(message.TotalTokens.Value, message.InputTokens.Value, message.OutputTokens.Value);
    //        }
    //    }
    //    finally
    //    {
    //        System.Console.ResetColor();
    //    }

    //    return ValueTask.CompletedTask;
    //}

    public void DisplayProgress(string message)
    {
        try
        {
            System.Console.ForegroundColor = ConsoleColor.Cyan;
            System.Console.WriteLine($"\n[{message}]");
        }
        finally
        {
            System.Console.ResetColor();
        }
    }

    public void DisplayTotalUsage()
    {
        System.Console.ForegroundColor = ConsoleColor.DarkCyan;
        System.Console.WriteLine($"[Token Usage: Total: {this._totalTokens}, Input: {this._inputTokens}, Output: {this._outputTokens}]");
    }

    private void DisplayUsage(int totalTokens, int inputTokens, int outputTokens)
    {
        this._totalTokens += totalTokens;
        this._inputTokens += inputTokens;
        this._outputTokens += outputTokens;
        System.Console.ForegroundColor = ConsoleColor.DarkCyan;
        System.Console.WriteLine($"[Token Usage: Total: {totalTokens}, Input: {inputTokens}, Output: {outputTokens}]");
    }

    /// <inheritdoc/>
    private ValueTask DisplayMessageAsync(ChatMessageContent message, ConsoleColor messageColor)
    {
        try
        {
            System.Console.ForegroundColor = ConsoleColor.Cyan;
            System.Console.WriteLine($"\n{message.AuthorName ?? AuthorRole.Assistant.Label}>");
            System.Console.ForegroundColor = messageColor;
            System.Console.WriteLine(message.Content);

            //ChatTokenUsage? usage = message.GetUsage(); // %%% TODO: Usage
            //if (usage != null)
            //{
            //    this.DisplayUsage(usage.TotalTokenCount, usage.InputTokenCount, usage.OutputTokenCount);
            //}
        }
        finally
        {
            System.Console.ResetColor();
        }

        return ValueTask.CompletedTask;
    }
}
