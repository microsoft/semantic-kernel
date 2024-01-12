// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.coreskills;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionInputAttribute;
import com.microsoft.semantickernel.text.TextChunker;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;
import java.util.List;
import javax.annotation.Nullable;
import reactor.core.publisher.Mono;

/** Semantic skill that enables conversations summarization */
public class ConversationSummarySkill {
    // The max tokens to process in a single semantic function call.
    private static final int MaxTokens = 1024;

    private final CompletionSKFunction summarizeConversationFunction;
    private final CompletionSKFunction conversationActionItemsFunction;
    private final CompletionSKFunction conversationTopicsFunction;
    private final Kernel kernel;

    /**
     * Initializes a new instance of the ConversationSummarySkill class
     *
     * @param kernel Kernel instance
     */
    public ConversationSummarySkill(Kernel kernel) {
        this.kernel = kernel;
        this.summarizeConversationFunction =
                SKBuilders.completionFunctions()
                        .withKernel(kernel)
                        .withPromptTemplate(
                                SemanticFunctionConstants.SummarizeConversationDefinition)
                        .withFunctionName("summarize")
                        .withSkillName("ConversationSummarySkill")
                        .withDescription(
                                "Given a section of a conversation transcript, summarize the part"
                                        + " of the conversation.")
                        .withCompletionConfig(
                                SKBuilders.completionConfig()
                                        .maxTokens(MaxTokens)
                                        .temperature(0.1)
                                        .topP(0.5)
                                        .build())
                        .build();

        this.conversationActionItemsFunction =
                SKBuilders.completionFunctions()
                        .withKernel(kernel)
                        .withPromptTemplate(
                                SemanticFunctionConstants.GetConversationActionItemsDefinition)
                        .withFunctionName("ActionItems")
                        .withSkillName("ConversationSummarySkill")
                        .withDescription(
                                "Given a section of a conversation transcript, identify action"
                                        + " items.")
                        .withCompletionConfig(
                                SKBuilders.completionConfig()
                                        .maxTokens(MaxTokens)
                                        .temperature(0.1)
                                        .topP(0.5)
                                        .build())
                        .build();

        this.conversationTopicsFunction =
                SKBuilders.completionFunctions()
                        .withKernel(kernel)
                        .withPromptTemplate(
                                SemanticFunctionConstants.GetConversationTopicsDefinition)
                        .withFunctionName("Topics")
                        .withSkillName("ConversationSummarySkill")
                        .withDescription(
                                "Analyze a conversation transcript and extract key topics worth"
                                        + " remembering.")
                        .withCompletionConfig(
                                SKBuilders.completionConfig()
                                        .maxTokens(MaxTokens)
                                        .temperature(0.1)
                                        .topP(0.5)
                                        .build())
                        .build();
    }

    /**
     * Given a long conversation transcript, summarize the conversation
     *
     * @param input A long conversation transcript
     * @param context The SKContext for function execution
     * @return A context containing the summarized conversation
     */
    @DefineSKFunction(
            description = "Given a long conversation transcript, summarize the conversation.",
            name = "SummarizeConversation")
    public Mono<SKContext> summarizeConversationAsync(
            @SKFunctionInputAttribute(description = "A long conversation transcript.") String input,
            @Nullable SKContext context) {
        List<String> lines = TextChunker.splitPlainTextLines(input, MaxTokens);
        List<String> paragraphs = TextChunker.splitPlainTextParagraphs(lines, MaxTokens);

        if (context == null) {
            context = SKBuilders.context().withSkills(kernel.getSkills()).build();
        }

        SKContext completionContext = context.copy();

        return this.summarizeConversationFunction.aggregatePartitionedResultsAsync(
                paragraphs, completionContext);
    }

    /**
     * Given a long conversation transcript, identify action items
     *
     * @param input A long conversation transcript
     * @param context The SKContext for function execution
     * @return A context containing the action items
     */
    @DefineSKFunction(
            description = "Given a long conversation transcript, identify action items.",
            name = "GetConversationActionItems")
    public Mono<SKContext> getConversationActionItemsAsync(
            @SKFunctionInputAttribute(description = "A long conversation transcript.") String input,
            SKContext context) {
        List<String> lines = TextChunker.splitPlainTextLines(input, MaxTokens);
        List<String> paragraphs = TextChunker.splitPlainTextParagraphs(lines, MaxTokens);

        SKContext completionContext = context.copy();

        return this.conversationActionItemsFunction.aggregatePartitionedResultsAsync(
                paragraphs, completionContext);
    }

    /**
     * Given a long conversation transcript, identify topics
     *
     * @param input A long conversation transcript
     * @param context The SKContext for function execution
     * @return A context containing the topics
     */
    @DefineSKFunction(
            description =
                    "Given a long conversation transcript, identify topics worth remembering.",
            name = "GetConversationTopics")
    public Mono<SKContext> getConversationTopicsAsync(
            @SKFunctionInputAttribute(description = "A long conversation transcript.") String input,
            SKContext context) {
        List<String> lines = TextChunker.splitPlainTextLines(input, MaxTokens);
        List<String> paragraphs = TextChunker.splitPlainTextParagraphs(lines, MaxTokens);

        SKContext completionContext = context.copy();

        return this.conversationTopicsFunction.aggregatePartitionedResultsAsync(
                paragraphs, completionContext);
    }
}
