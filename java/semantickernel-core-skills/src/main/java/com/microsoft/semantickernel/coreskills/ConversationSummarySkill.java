// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.coreskills;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionInputAttribute;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters;
import com.microsoft.semantickernel.text.TextChunker;
import com.microsoft.semantickernel.textcompletion.CompletionSKContext;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;

import reactor.core.publisher.Mono;

import java.util.List;

import javax.annotation.Nullable;

/** Semantic skill that enables conversations summarization */
public class ConversationSummarySkill {
    // The max tokens to process in a single semantic function call.
    private static final int MaxTokens = 1024;

    private final CompletionSKFunction summarizeConversationFunction;
    private final CompletionSKFunction conversationActionItemsFunction;
    private final CompletionSKFunction conversationTopicsFunction;

    /**
     * Initializes a new instance of the ConversationSummarySkill class
     *
     * @param kernel Kernel instance
     */
    public ConversationSummarySkill(Kernel kernel) {
        this.summarizeConversationFunction =
                SKBuilders.completionFunctions(kernel)
                        .createFunction(
                                SemanticFunctionConstants.SummarizeConversationDefinition,
                                "summarize",
                                "ConversationSummarySkill",
                                "Given a section of a conversation transcript, summarize the part"
                                        + " of the conversation.",
                                SKBuilders.completionConfig()
                                        .maxTokens(MaxTokens)
                                        .temperature(0.1)
                                        .topP(0.5)
                                        .build());

        this.conversationActionItemsFunction =
                SKBuilders.completionFunctions(kernel)
                        .createFunction(
                                SemanticFunctionConstants.GetConversationActionItemsDefinition,
                                "ActionItems",
                                "ConversationSummarySkill",
                                "Given a section of a conversation transcript, identify action"
                                        + " items.",
                                SKBuilders.completionConfig()
                                        .maxTokens(MaxTokens)
                                        .temperature(0.1)
                                        .topP(0.5)
                                        .build());

        this.conversationTopicsFunction =
                SKBuilders.completionFunctions(kernel)
                        .createFunction(
                                SemanticFunctionConstants.GetConversationTopicsDefinition,
                                "Topics",
                                "ConversationSummarySkill",
                                "Analyze a conversation transcript and extract key topics worth"
                                        + " remembering.",
                                SKBuilders.completionConfig()
                                        .maxTokens(MaxTokens)
                                        .temperature(0.1)
                                        .topP(0.5)
                                        .build());
    }

    /**
     * Given a long conversation transcript, summarize the conversation
     *
     * @param input A long conversation transcript
     * @param context The SKContext for function execution
     * @return
     */
    @DefineSKFunction(
            description = "Given a long conversation transcript, summarize the conversation.",
            name = "SummarizeConversation")
    public Mono<CompletionSKContext> summarizeConversationAsync(
            @SKFunctionInputAttribute
                    @SKFunctionParameters(
                            description = "A long conversation transcript.",
                            name = "input")
                    String input,
            @Nullable SKContext<?> context) {
        List<String> lines = TextChunker.splitPlainTextLines(input, MaxTokens);
        List<String> paragraphs = TextChunker.splitPlainTextParagraphs(lines, MaxTokens);

        CompletionSKContext completionContext = summarizeConversationFunction.buildContext(context);

        return this.summarizeConversationFunction.aggregatePartitionedResultsAsync(
                paragraphs, completionContext);
    }

    /**
     * Given a long conversation transcript, identify action items
     *
     * @param input A long conversation transcript
     * @param context The SKContext for function execution
     * @return
     */
    @DefineSKFunction(
            description = "Given a long conversation transcript, identify action items.",
            name = "GetConversationActionItems")
    public Mono<CompletionSKContext> getConversationActionItemsAsync(
            @SKFunctionInputAttribute
                    @SKFunctionParameters(
                            description = "A long conversation transcript.",
                            name = "input")
                    String input,
            SKContext<?> context) {
        List<String> lines = TextChunker.splitPlainTextLines(input, MaxTokens);
        List<String> paragraphs = TextChunker.splitPlainTextParagraphs(lines, MaxTokens);

        CompletionSKContext completionContext = summarizeConversationFunction.buildContext(context);

        return this.conversationActionItemsFunction.aggregatePartitionedResultsAsync(
                paragraphs, completionContext);
    }

    /**
     * Given a long conversation transcript, identify topics
     *
     * @param input A long conversation transcript
     * @param context The SKContext for function execution
     * @return
     */
    @DefineSKFunction(
            description =
                    "Given a long conversation transcript, identify topics worth remembering.",
            name = "GetConversationTopics")
    public Mono<CompletionSKContext> getConversationTopicsAsync(
            @SKFunctionInputAttribute
                    @SKFunctionParameters(
                            description = "A long conversation transcript.",
                            name = "input")
                    String input,
            SKContext<?> context) {
        List<String> lines = TextChunker.splitPlainTextLines(input, MaxTokens);
        List<String> paragraphs = TextChunker.splitPlainTextParagraphs(lines, MaxTokens);

        CompletionSKContext completionContext = summarizeConversationFunction.buildContext(context);

        return this.conversationTopicsFunction.aggregatePartitionedResultsAsync(
                paragraphs, completionContext);
    }
}
