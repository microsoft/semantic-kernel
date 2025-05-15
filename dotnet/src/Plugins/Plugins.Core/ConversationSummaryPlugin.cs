// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.ComponentModel;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Plugins.Core;

/// <summary>
/// Semantic plugin that enables conversations summarization.
/// </summary>
public class ConversationSummaryPlugin
{
    /// <summary>
    /// The max tokens to process in a single prompt function call.
    /// </summary>
    private const int MaxTokens = 1024;

    private readonly KernelFunction _summarizeConversationFunction;
    private readonly KernelFunction _conversationActionItemsFunction;
    private readonly KernelFunction _conversationTopicsFunction;

    /// <summary>
    /// Initializes a new instance of the <see cref="ConversationSummaryPlugin"/> class.
    /// </summary>
    public ConversationSummaryPlugin()
    {
        PromptExecutionSettings settings = new()
        {
            ExtensionData = new Dictionary<string, object>()
            {
                { "Temperature", 0.1 },
                { "TopP", 0.5 },
                { "MaxTokens", MaxTokens }
            }
        };

        this._summarizeConversationFunction = KernelFunctionFactory.CreateFromPrompt(
            PromptFunctionConstants.SummarizeConversationDefinition,
            description: "Given a section of a conversation transcript, summarize the part of the conversation.",
            executionSettings: settings);

        this._conversationActionItemsFunction = KernelFunctionFactory.CreateFromPrompt(
            PromptFunctionConstants.GetConversationActionItemsDefinition,
            description: "Given a section of a conversation transcript, identify action items.",
            executionSettings: settings);

        this._conversationTopicsFunction = KernelFunctionFactory.CreateFromPrompt(
            PromptFunctionConstants.GetConversationTopicsDefinition,
            description: "Analyze a conversation transcript and extract key topics worth remembering.",
            executionSettings: settings);
    }

    /// <summary>
    /// Given a long conversation transcript, summarize the conversation.
    /// </summary>
    /// <param name="input">A long conversation transcript.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    [KernelFunction, Description("Given a long conversation transcript, summarize the conversation.")]
    public Task<string> SummarizeConversationAsync(
        [Description("A long conversation transcript.")] string input,
        Kernel kernel) =>
        ProcessAsync(this._summarizeConversationFunction, input, kernel);

    /// <summary>
    /// Given a long conversation transcript, identify action items.
    /// </summary>
    /// <param name="input">A long conversation transcript.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    [KernelFunction, Description("Given a long conversation transcript, identify action items.")]
    public Task<string> GetConversationActionItemsAsync(
        [Description("A long conversation transcript.")] string input,
        Kernel kernel) =>
        ProcessAsync(this._conversationActionItemsFunction, input, kernel);

    /// <summary>
    /// Given a long conversation transcript, identify topics.
    /// </summary>
    /// <param name="input">A long conversation transcript.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    [KernelFunction, Description("Given a long conversation transcript, identify topics worth remembering.")]
    public Task<string> GetConversationTopicsAsync(
        [Description("A long conversation transcript.")] string input,
        Kernel kernel) =>
        ProcessAsync(this._conversationTopicsFunction, input, kernel);

    private static async Task<string> ProcessAsync(KernelFunction func, string input, Kernel kernel)
    {
#pragma warning disable SKEXP0050 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
        List<string> lines = TextChunker.SplitPlainTextLines(input, MaxTokens);
        List<string> paragraphs = TextChunker.SplitPlainTextParagraphs(lines, MaxTokens);
#pragma warning restore SKEXP0050 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

        string[] results = new string[paragraphs.Count];

        for (int i = 0; i < results.Length; i++)
        {
            // The first parameter is the input text.
            results[i] = (await func.InvokeAsync(kernel, new() { ["input"] = paragraphs[i] }).ConfigureAwait(false))
                .GetValue<string>() ?? string.Empty;
        }

        return string.Join("\n", results);
    }
}
