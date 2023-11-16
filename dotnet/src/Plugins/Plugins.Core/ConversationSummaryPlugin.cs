// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.ComponentModel;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Plugins.Core;

/// <summary>
/// Semantic plugin that enables conversations summarization.
/// </summary>
public class ConversationSummaryPlugin
{
    /// <summary>
    /// The max tokens to process in a single semantic function call.
    /// </summary>
    private const int MaxTokens = 1024;

    private readonly ISKFunction _summarizeConversationFunction;
    private readonly ISKFunction _conversationActionItemsFunction;
    private readonly ISKFunction _conversationTopicsFunction;

    /// <summary>
    /// Initializes a new instance of the <see cref="ConversationSummaryPlugin"/> class.
    /// </summary>
    public ConversationSummaryPlugin()
    {
        this._summarizeConversationFunction = SKFunction.FromPrompt(
            SemanticFunctionConstants.SummarizeConversationDefinition,
            description: "Given a section of a conversation transcript, summarize the part of the conversation.",
            requestSettings: new AIRequestSettings()
            {
                ExtensionData = new Dictionary<string, object>()
                {
                    { "Temperature", 0.1 },
                    { "TopP", 0.5 },
                    { "MaxTokens", MaxTokens }
                }
            });

        this._conversationActionItemsFunction = SKFunction.FromPrompt(
            SemanticFunctionConstants.GetConversationActionItemsDefinition,
            description: "Given a section of a conversation transcript, identify action items.",
            requestSettings: new AIRequestSettings()
            {
                ExtensionData = new Dictionary<string, object>()
                {
                    { "Temperature", 0.1 },
                    { "TopP", 0.5 },
                    { "MaxTokens", MaxTokens }
                }
            });

        this._conversationTopicsFunction = SKFunction.FromPrompt(
            SemanticFunctionConstants.GetConversationTopicsDefinition,
            description: "Analyze a conversation transcript and extract key topics worth remembering.",
            requestSettings: new AIRequestSettings()
            {
                ExtensionData = new Dictionary<string, object>()
                {
                    { "Temperature", 0.1 },
                    { "TopP", 0.5 },
                    { "MaxTokens", MaxTokens }
                }
            });
    }

    /// <summary>
    /// Given a long conversation transcript, summarize the conversation.
    /// </summary>
    /// <param name="input">A long conversation transcript.</param>
    /// <param name="kernel">The kernel</param>
    /// <param name="context">The SKContext for function execution.</param>
    [SKFunction, Description("Given a long conversation transcript, summarize the conversation.")]
    public Task<SKContext> SummarizeConversationAsync(
        [Description("A long conversation transcript.")] string input,
        Kernel kernel,
        SKContext context)
    {
        List<string> lines = TextChunker.SplitPlainTextLines(input, MaxTokens);
        List<string> paragraphs = TextChunker.SplitPlainTextParagraphs(lines, MaxTokens);

        return this._summarizeConversationFunction
            .AggregatePartitionedResultsAsync(kernel, paragraphs, context);
    }

    /// <summary>
    /// Given a long conversation transcript, identify action items.
    /// </summary>
    /// <param name="input">A long conversation transcript.</param>
    /// <param name="kernel">The kernel.</param>
    /// <param name="context">The SKContext for function execution.</param>
    [SKFunction, Description("Given a long conversation transcript, identify action items.")]
    public Task<SKContext> GetConversationActionItemsAsync(
        [Description("A long conversation transcript.")] string input,
        Kernel kernel,
        SKContext context)
    {
        List<string> lines = TextChunker.SplitPlainTextLines(input, MaxTokens);
        List<string> paragraphs = TextChunker.SplitPlainTextParagraphs(lines, MaxTokens);

        return this._conversationActionItemsFunction
            .AggregatePartitionedResultsAsync(kernel, paragraphs, context);
    }

    /// <summary>
    /// Given a long conversation transcript, identify topics.
    /// </summary>
    /// <param name="input">A long conversation transcript.</param>
    /// <param name="kernel">The kernel.</param>
    /// <param name="context">The SKContext for function execution.</param>
    [SKFunction, Description("Given a long conversation transcript, identify topics worth remembering.")]
    public Task<SKContext> GetConversationTopicsAsync(
        [Description("A long conversation transcript.")] string input,
        Kernel kernel,
        SKContext context)
    {
        List<string> lines = TextChunker.SplitPlainTextLines(input, MaxTokens);
        List<string> paragraphs = TextChunker.SplitPlainTextParagraphs(lines, MaxTokens);

        return this._conversationTopicsFunction
            .AggregatePartitionedResultsAsync(kernel, paragraphs, context);
    }
}
