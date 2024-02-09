package com.microsoft.semantickernel.aiservices.openai.chatcompletion;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.models.ChatChoice;
import com.azure.ai.openai.models.ChatCompletions;
import com.azure.ai.openai.models.ChatCompletionsFunctionToolCall;
import com.azure.ai.openai.models.ChatCompletionsOptions;
import com.azure.ai.openai.models.ChatCompletionsToolCall;
import com.azure.ai.openai.models.ChatRequestAssistantMessage;
import com.azure.ai.openai.models.ChatRequestMessage;
import com.azure.ai.openai.models.ChatRequestSystemMessage;
import com.azure.ai.openai.models.ChatRequestToolMessage;
import com.azure.ai.openai.models.ChatRequestUserMessage;
import com.azure.ai.openai.models.ChatResponseMessage;
import com.azure.ai.openai.models.FunctionDefinition;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.chatcompletion.AuthorRole;
import com.microsoft.semantickernel.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.chatcompletion.ChatMessageContent;
import com.microsoft.semantickernel.exceptions.AIException;
import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.orchestration.FunctionResultMetadata;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;
import javax.annotation.Nullable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public class OpenAIChatCompletion implements ChatCompletionService {

    private static final Logger LOGGER = LoggerFactory.getLogger(OpenAIChatCompletion.class);
    private final OpenAIAsyncClient client;
    private final Map<String, ContextVariable<?>> attributes;
    private final String serviceId;

    public OpenAIChatCompletion(OpenAIAsyncClient client, String modelId, String serviceId) {
        this.serviceId = serviceId;
        this.client = client;
        this.attributes = new HashMap<>();
        attributes.put(MODEL_ID_KEY, ContextVariable.of(modelId));
    }

    public static Builder builder() {
        return new Builder();
    }

    @Override
    public Map<String, ContextVariable<?>> getAttributes() {
        return attributes;
    }

    @Override
    public String getServiceId() {
        return serviceId;
    }

    @Override
    public Mono<List<ChatMessageContent>> getChatMessageContentsAsync(ChatHistory chatHistory,
        @Nullable PromptExecutionSettings promptExecutionSettings, @Nullable Kernel kernel) {

        List<ChatRequestMessage> chatRequestMessages = getChatRequestMessages(chatHistory);
        return internalChatMessageContentsAsync(chatRequestMessages, promptExecutionSettings,
            kernel);
    }

    @Override
    public Mono<List<ChatMessageContent>> getChatMessageContentsAsync(String prompt,
        PromptExecutionSettings promptExecutionSettings, Kernel kernel) {
        ParsedPrompt parsedPrompt = XMLPromptParser.parse(prompt);

        return internalChatMessageContentsAsync(
            parsedPrompt.getChatRequestMessages(),
            promptExecutionSettings,
            kernel);
    }

    private Mono<List<ChatMessageContent>> internalChatMessageContentsAsync(
        List<ChatRequestMessage> messages,
        PromptExecutionSettings settings,
        Kernel kernel) {

        List<FunctionDefinition> functions = new ArrayList<>();
        if (kernel != null) {
            kernel.getPlugins().forEach(plugin ->
                plugin.getFunctions().forEach((name, function) ->
                    functions.add(OpenAIFunction.toFunctionDefinition(function.getMetadata(),
                        plugin.getName()))
                )
            );
        }

        // Create copy to avoid reactor exceptions when updating the chat options messages internally
        ChatCompletionsOptions options = getCompletionsOptions(this, new ArrayList<>(messages),
            functions, settings);

        return internalChatMessageContentsAsync(
            kernel,
            options,
            Math.min(MAXIMUM_INFLIGHT_AUTO_INVOKES,
                settings != null && settings.getToolCallBehavior() != null
                    ? settings.getToolCallBehavior().getMaximumAutoInvokeAttempts() : 0)
        );
    }

    private Mono<List<ChatMessageContent>> internalChatMessageContentsAsync(
        Kernel kernel,
        ChatCompletionsOptions options,
        int autoInvokeAttempts) {
//        AtomicReference<ChatCompletionsOptions> options = new AtomicReference<>(chatCompletionsOptions);
        Mono<ChatCompletions> result = client.getChatCompletions(getModelId(), options);

        return result.flatMap(completions -> {
            List<ChatResponseMessage> responseMessages = completions
                .getChoices()
                .stream()
                .map(ChatChoice::getMessage)
                .filter(Objects::nonNull)
                .collect(Collectors.toList());

            // Just return the result:
            // If we don't want to attempt to invoke any functions
            // Or if we are auto-invoking, but we somehow end up with other than 1 choice even though only 1 was requested
            if (autoInvokeAttempts == 0 || responseMessages.size() != 1) {
                return getChatMessageContentsAsync(completions);
            }
            // Or if there are no tool calls to be done
            ChatResponseMessage response = responseMessages.get(0);
            List<ChatCompletionsToolCall> toolCalls = response.getToolCalls();
            if (toolCalls == null || toolCalls.isEmpty()) {
                return getChatMessageContentsAsync(completions);
            }

            ChatRequestAssistantMessage requestMessage = new ChatRequestAssistantMessage(
                response.getContent());
            requestMessage.setToolCalls(toolCalls);

            // Add the original assistant message to the chat options; this is required for the service
            // to understand the tool call responses
            options.getMessages().add(requestMessage);

            return Flux
                .fromIterable(toolCalls)
                .reduce(
                    Mono.just(options),
                    (opts, toolCall) -> {
                        if (toolCall instanceof ChatCompletionsFunctionToolCall) {
                            return opts
                                .flatMap(op -> {
                                    // OpenAI only supports function tool call at the moment
                                    ChatCompletionsFunctionToolCall functionToolCall = (ChatCompletionsFunctionToolCall) toolCall;
                                    return invokeFunctionTool(kernel, functionToolCall)
                                        .map(functionResult -> {
                                            // Add chat request tool message to the chat options
                                            ChatRequestMessage requestToolMessage = new ChatRequestToolMessage(
                                                functionResult.getResult(),
                                                functionToolCall.getId());
                                            op.getMessages().add(requestToolMessage);
                                            return op;
                                        });
                                });
                        }
                        return opts;
                    })
                .flatMap(op -> op)
                .flatMap(
                    op -> internalChatMessageContentsAsync(kernel, op, autoInvokeAttempts - 1));

        });
    }

    private Mono<FunctionResult<String>> invokeFunctionTool(Kernel kernel,
        ChatCompletionsFunctionToolCall toolCall) {
        // Split the full name of a function into plugin and function name
        String name = toolCall.getFunction().getName();
        String[] parts = name.split(OpenAIFunction.getNameSeparator());
        String pluginName = parts.length > 1 ? parts[0] : "";
        String fnName = parts.length > 1 ? parts[1] : parts[0];

        KernelFunction function = kernel.getPlugins().getFunction(pluginName, fnName);
        KernelArguments arguments = KernelArguments.builder().build();

        try {
            ObjectMapper mapper = new ObjectMapper();
            JsonNode jsonToolCallArguments = mapper.readTree(toolCall.getFunction().getArguments());

            jsonToolCallArguments.fields().forEachRemaining(
                entry -> arguments.put(entry.getKey(),
                    ContextVariable.of(entry.getValue().asText())));
        } catch (JsonProcessingException e) {
            LOGGER.error("Failed to parse json", e);
            return Mono.empty();
        }

        return function.invokeAsync(kernel, arguments,
            ContextVariableTypes.getDefaultVariableTypeForClass(String.class));
    }

    private Mono<List<ChatMessageContent>> getChatMessageContentsAsync(
        ChatCompletions completions) {
        FunctionResultMetadata completionMetadata = FunctionResultMetadata.build(
            completions.getId(),
            completions.getUsage(),
            completions.getCreatedAt());

        List<ChatResponseMessage> responseMessages = completions
            .getChoices()
            .stream()
            .map(ChatChoice::getMessage)
            .filter(Objects::nonNull)
            .collect(Collectors.toList());

        return Flux.fromIterable(responseMessages)
            .map(response -> new ChatMessageContent(
                AuthorRole.ASSISTANT,
                response.getContent(),
                this.getModelId(),
                null,
                null,
                completionMetadata)).collectList();
    }

    private static ChatCompletionsOptions getCompletionsOptions(
        ChatCompletionService chatCompletionService,
        List<ChatRequestMessage> chatRequestMessages,
        List<FunctionDefinition> functions,
        PromptExecutionSettings promptExecutionSettings) {

        ChatCompletionsOptions options = new ChatCompletionsOptions(chatRequestMessages)
            .setModel(chatCompletionService.getModelId());

        if (promptExecutionSettings == null) {
            return options;
        }

        if (promptExecutionSettings.getResultsPerPrompt() < 1
            || promptExecutionSettings.getResultsPerPrompt() > MAX_RESULTS_PER_PROMPT) {
            throw new AIException(AIException.ErrorCodes.INVALID_REQUEST,
                String.format("Results per prompt must be in range between 1 and %d, inclusive.",
                    MAX_RESULTS_PER_PROMPT));
        }

        if (promptExecutionSettings.getToolCallBehavior() != null) {
            promptExecutionSettings.getToolCallBehavior().configureOptions(options, functions);
        }

        Map<String, Integer> logit = null;
        if (promptExecutionSettings.getTokenSelectionBiases() != null) {
            logit = promptExecutionSettings
                .getTokenSelectionBiases()
                .entrySet()
                .stream()
                .collect(Collectors.toMap(
                    entry -> entry.getKey().toString(),
                    Map.Entry::getValue)
                );
        }

        options
            .setTemperature(promptExecutionSettings.getTemperature())
            .setTopP(promptExecutionSettings.getTopP())
            .setPresencePenalty(promptExecutionSettings.getPresencePenalty())
            .setFrequencyPenalty(promptExecutionSettings.getFrequencyPenalty())
            .setPresencePenalty(promptExecutionSettings.getPresencePenalty())
            .setMaxTokens(promptExecutionSettings.getMaxTokens())
            .setN(promptExecutionSettings.getResultsPerPrompt())
            // Azure OpenAI WithData API does not allow to send empty array of stop sequences
            // Gives back "Validation error at #/stop/str: Input should be a valid string\nValidation error at #/stop/list[str]: List should have at least 1 item after validation, not 0"
            .setStop(promptExecutionSettings.getStopSequences() == null
                || promptExecutionSettings.getStopSequences().isEmpty() ? null
                : promptExecutionSettings.getStopSequences())
            .setUser(promptExecutionSettings.getUser())
            .setLogitBias(logit);

        return options;
    }

    private static List<ChatRequestMessage> getChatRequestMessages(ChatHistory chatHistory) {
        List<ChatMessageContent> messages = chatHistory.getMessages();
        if (messages == null || messages.isEmpty()) {
            return new ArrayList<>();
        }
        return messages.stream()
            .map(message -> {
                AuthorRole authorRole = message.getAuthorRole();
                String content = message.getContent();
                return getChatRequestMessage(authorRole, content);
            })
            .collect(Collectors.toList());
    }


    static ChatRequestMessage getChatRequestMessage(
        AuthorRole authorRole,
        String content) {

        switch (authorRole) {
            case ASSISTANT:
                return new ChatRequestAssistantMessage(content);
            case SYSTEM:
                return new ChatRequestSystemMessage(content);
            case USER:
                return new ChatRequestUserMessage(content);
            case TOOL:
                return new ChatRequestToolMessage(content, null);
            default:
                LOGGER.debug("Unexpected author role: " + authorRole);
                return null;
        }

    }

    public static class Builder extends ChatCompletionService.Builder {

        @Override
        public OpenAIChatCompletion build() {
            return new OpenAIChatCompletion(client, modelId, serviceId);
        }
    }
}
