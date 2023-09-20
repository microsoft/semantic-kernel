// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.ComponentModel;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Plugins.Core;

/// <summary>
/// <para>Semantic skill that enables conversations summarization.</para>
/// </summary>
/// <example>
/// <code>
/// var kernel Kernel.Builder.Build();
/// kernel.ImportSkill(new ConversationSummaryPlugin(kernel));
/// </code>
/// </example>
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
    /// <param name="kernel">Kernel instance</param>
    public ConversationSummaryPlugin(IKernel kernel)
    {
        this._summarizeConversationFunction = kernel.CreateSemanticFunction(
            SemanticFunctionConstants.SummarizeConversationDefinition,
            skillName: nameof(ConversationSummaryPlugin),
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

        this._conversationActionItemsFunction = kernel.CreateSemanticFunction(
            SemanticFunctionConstants.GetConversationActionItemsDefinition,
            skillName: nameof(ConversationSummaryPlugin),
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

        this._conversationTopicsFunction = kernel.CreateSemanticFunction(
            SemanticFunctionConstants.GetConversationTopicsDefinition,
            skillName: nameof(ConversationSummaryPlugin),
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
    /// <param name="context">The SKContext for function execution.</param>
    [SKFunction, Description("Given a long conversation transcript, summarize the conversation.")]
    public Task<SKContext> SummarizeConversationAsync(
        [Description("A long conversation transcript.")] string input,
        SKContext context)
    {
        List<string> lines = TextChunker.SplitPlainTextLines(input, MaxTokens);
        List<string> paragraphs = TextChunker.SplitPlainTextParagraphs(lines, MaxTokens);

        return this._summarizeConversationFunction
            .AggregatePartitionedResultsAsync(paragraphs, context);
    }

    /// <summary>
    /// Given a long conversation transcript, identify action items.
    /// </summary>
    /// <param name="input">A long conversation transcript.</param>
    /// <param name="context">The SKContext for function execution.</param>
    [SKFunction, Description("Given a long conversation transcript, identify action items.")]
    public Task<SKContext> GetConversationActionItemsAsync(
        [Description("A long conversation transcript.")] string input,
        SKContext context)
    {
        List<string> lines = TextChunker.SplitPlainTextLines(input, MaxTokens);
        List<string> paragraphs = TextChunker.SplitPlainTextParagraphs(lines, MaxTokens);

        return this._conversationActionItemsFunction
            .AggregatePartitionedResultsAsync(paragraphs, context);
    }

    /// <summary>
    /// Given a long conversation transcript, identify topics.
    /// </summary>
    /// <param name="input">A long conversation transcript.</param>
    /// <param name="context">The SKContext for function execution.</param>
    [SKFunction, Description("Given a long conversation transcript, identify topics worth remembering.")]
    public Task<SKContext> GetConversationTopicsAsync(
        [Description("A long conversation transcript.")] string input,
        SKContext context)
    {
        List<string> lines = TextChunker.SplitPlainTextLines(input, MaxTokens);
        List<string> paragraphs = TextChunker.SplitPlainTextParagraphs(lines, MaxTokens);

        return this._conversationTopicsFunction
            .AggregatePartitionedResultsAsync(paragraphs, context);
    }
}
