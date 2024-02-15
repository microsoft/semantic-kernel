package com.microsoft.semantickernel.samples.plugins;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.KernelFunctionArguments;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes;
import com.microsoft.semantickernel.plugin.annotations.DefineKernelFunction;
import com.microsoft.semantickernel.plugin.annotations.KernelFunctionParameter;
import com.microsoft.semantickernel.text.TextChunker;
import java.util.List;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/// <summary>
/// Semantic plugin that enables conversations summarization.
/// </summary>
public class ConversationSummaryPlugin {

    /// <summary>
    /// The max tokens to process in a single prompt function call.
    /// </summary>
    private static final int MaxTokens = 1024;

    private KernelFunction<String> summarizeConversationFunction;
    private KernelFunction<String> conversationActionItemsFunction;
    private KernelFunction<String> conversationTopicsFunction;

    /// <summary>
    /// Initializes a new instance of the <see cref="ConversationSummaryPlugin"/> class.
    /// </summary>
    public ConversationSummaryPlugin() {
        PromptExecutionSettings settings = PromptExecutionSettings.builder()
            .withMaxTokens(MaxTokens)
            .withTemperature(0.1)
            .withTopP(0.5)
            .build();

        this.summarizeConversationFunction = KernelFunction
            .<String>createFromPrompt(PromptFunctionConstants.SummarizeConversationDefinition)
            .withDefaultExecutionSettings(settings)
            .withName("summarizeConversation")
            .withDescription(
                "Given a section of a conversation transcript, summarize the part of the conversation.")
            .build();

        this.conversationActionItemsFunction = KernelFunction
            .<String>createFromPrompt(PromptFunctionConstants.GetConversationActionItemsDefinition)
            .withDefaultExecutionSettings(settings)
            .withName("conversationActionItems")
            .withDescription("Given a section of a conversation transcript, identify action items.")
            .build();

        this.conversationTopicsFunction = KernelFunction
            .<String>createFromPrompt(PromptFunctionConstants.GetConversationTopicsDefinition)
            .withDefaultExecutionSettings(settings)
            .withName("conversationTopics")
            .withDescription(
                "Analyze a conversation transcript and extract key topics worth remembering.")
            .build();
    }

    /// <summary>
    /// Given a long conversation transcript, summarize the conversation.
    /// </summary>
    /// <param name="input">A long conversation transcript.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    @DefineKernelFunction(description = "Given a long conversation transcript, summarize the conversation.", name = "SummarizeConversation", returnType = "java.lang.String")
    public Mono<String> SummarizeConversationAsync(
        @KernelFunctionParameter(description = "A long conversation transcript.", name = "input") String input,
        Kernel kernel) {
        return processAsync(this.summarizeConversationFunction, input, kernel);
    }

    /// <summary>
    /// Given a long conversation transcript, identify action items.
    /// </summary>
    /// <param name="input">A long conversation transcript.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    @DefineKernelFunction(description = "Given a long conversation transcript, identify action items.", name = "GetConversationActionItems", returnType = "java.lang.String")
    public Mono<String> GetConversationActionItemsAsync(
        @KernelFunctionParameter(description = "A long conversation transcript.", name = "input") String input,
        Kernel kernel) {
        return processAsync(this.conversationActionItemsFunction, input, kernel);
    }

    /// <summary>
    /// Given a long conversation transcript, identify topics.
    /// </summary>
    /// <param name="input">A long conversation transcript.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    @DefineKernelFunction(description = "Given a long conversation transcript, identify topics worth remembering.", name = "GetConversationTopics", returnType = "java.lang.String")

    public Mono<String> GetConversationTopicsAsync(
        @KernelFunctionParameter(description = "A long conversation transcript.", name = "input") String input,
        Kernel kernel) {
        return processAsync(this.conversationTopicsFunction, input, kernel);
    }

    private static Mono<String> processAsync(KernelFunction<String> func, String input,
        Kernel kernel) {
        List<String> lines = TextChunker.splitPlainTextLines(input, MaxTokens);
        List<String> paragraphs = TextChunker.splitPlainTextParagraphs(lines, MaxTokens);

        return Flux.fromIterable(paragraphs)
            .concatMap(paragraph -> {
                // The first parameter is the input text.
                return func.invokeAsync(kernel)
                    .withArguments(
                        new KernelFunctionArguments.Builder()
                            .withInput(paragraph)
                            .build())
                    .withResultType(
                        ContextVariableTypes.getGlobalVariableTypeForClass(String.class));
            })
            .reduce("", (acc, next) -> {
                return acc + "\n" + next.getResult();
            });
    }
}
