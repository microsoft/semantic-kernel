package com.microsoft.semantickernel.samples.plugins;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes;
import com.microsoft.semantickernel.orchestration.contextvariables.DefaultKernelArguments;
import com.microsoft.semantickernel.plugin.KernelFunctionFactory;
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

    private KernelFunction summarizeConversationFunction;
    private KernelFunction conversationActionItemsFunction;
    private KernelFunction conversationTopicsFunction;

    /// <summary>
    /// Initializes a new instance of the <see cref="ConversationSummaryPlugin"/> class.
    /// </summary>
    public ConversationSummaryPlugin() {
        PromptExecutionSettings settings = PromptExecutionSettings.builder()
            .withMaxTokens(MaxTokens)
            .withTemperature(0.1)
            .withTopP(0.5)
            .build();

        this.summarizeConversationFunction = KernelFunctionFactory.createFromPrompt(
            PromptFunctionConstants.SummarizeConversationDefinition,
            settings,
            "summarizeConversation",
            "Given a section of a conversation transcript, summarize the part of the conversation.",
            null,
            null);

        this.conversationActionItemsFunction = KernelFunctionFactory.createFromPrompt(
            PromptFunctionConstants.GetConversationActionItemsDefinition,
            settings,
            "conversationActionItems",
            "Given a section of a conversation transcript, identify action items.",
            null,
            null);

        this.conversationTopicsFunction = KernelFunctionFactory.createFromPrompt(
            PromptFunctionConstants.GetConversationTopicsDefinition,
            settings,
            "conversationTopics",
            "Analyze a conversation transcript and extract key topics worth remembering.",
            null,
            null);
    }

    /// <summary>
    /// Given a long conversation transcript, summarize the conversation.
    /// </summary>
    /// <param name="input">A long conversation transcript.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    @DefineKernelFunction(
        description = "Given a long conversation transcript, summarize the conversation.",
        name = "SummarizeConversation"
    )
    public Mono<String> SummarizeConversationAsync(
        @KernelFunctionParameter(
            description = "A long conversation transcript.",
            name = "input"
        )
        String input,
        Kernel kernel) {
        return processAsync(this.summarizeConversationFunction, input, kernel);
    }

    /// <summary>
    /// Given a long conversation transcript, identify action items.
    /// </summary>
    /// <param name="input">A long conversation transcript.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    @DefineKernelFunction(
        description = "Given a long conversation transcript, identify action items.",
        name = "GetConversationActionItems"
    )
    public Mono<String> GetConversationActionItemsAsync(
        @KernelFunctionParameter(
            description = "A long conversation transcript.",
            name = "input"
        )
        String input,
        Kernel kernel) {
        return processAsync(this.conversationActionItemsFunction, input, kernel);
    }

    /// <summary>
    /// Given a long conversation transcript, identify topics.
    /// </summary>
    /// <param name="input">A long conversation transcript.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    @DefineKernelFunction(
        description = "Given a long conversation transcript, identify topics worth remembering.",
        name = "GetConversationTopics"
    )

    public Mono<String> GetConversationTopicsAsync(
        @KernelFunctionParameter(
            description = "A long conversation transcript.",
            name = "input"
        )
        String input,
        Kernel kernel) {
        return processAsync(this.conversationTopicsFunction, input, kernel);
    }

    private static Mono<String> processAsync(KernelFunction func, String input, Kernel kernel) {
        List<String> lines = TextChunker.splitPlainTextLines(input, MaxTokens);
        List<String> paragraphs = TextChunker.splitPlainTextParagraphs(lines, MaxTokens);

        return Flux.fromIterable(paragraphs)
            .concatMap(paragraph -> {
                // The first parameter is the input text.
                return func.invokeAsync(kernel,
                    new DefaultKernelArguments.Builder()
                        .withInput(paragraph)
                        .build(),
                    ContextVariableTypes.getDefaultVariableTypeForClass(String.class));
            })
            .reduce("", (acc, next) -> {
                return acc + "\n" + next.getValue();
            });
    }
}
