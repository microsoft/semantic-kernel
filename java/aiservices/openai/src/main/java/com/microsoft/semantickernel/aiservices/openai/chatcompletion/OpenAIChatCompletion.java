// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.aiservices.openai.chatcompletion;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.models.ChatChoice;
import com.azure.ai.openai.models.ChatCompletions;
import com.azure.ai.openai.models.ChatCompletionsFunctionToolCall;
import com.azure.ai.openai.models.ChatCompletionsFunctionToolDefinition;
import com.azure.ai.openai.models.ChatCompletionsJsonResponseFormat;
import com.azure.ai.openai.models.ChatCompletionsOptions;
import com.azure.ai.openai.models.ChatCompletionsTextResponseFormat;
import com.azure.ai.openai.models.ChatCompletionsToolCall;
import com.azure.ai.openai.models.ChatCompletionsToolDefinition;
import com.azure.ai.openai.models.ChatRequestAssistantMessage;
import com.azure.ai.openai.models.ChatRequestMessage;
import com.azure.ai.openai.models.ChatRequestSystemMessage;
import com.azure.ai.openai.models.ChatRequestToolMessage;
import com.azure.ai.openai.models.ChatRequestUserMessage;
import com.azure.ai.openai.models.ChatResponseMessage;
import com.azure.ai.openai.models.FunctionCall;
import com.azure.core.util.BinaryData;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ContainerNode;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.openai.OpenAiService;
import com.microsoft.semantickernel.aiservices.openai.implementation.OpenAIRequestSettings;
import com.microsoft.semantickernel.contextvariables.ContextVariable;
import com.microsoft.semantickernel.contextvariables.ContextVariableTypes;
import com.microsoft.semantickernel.exceptions.AIException;
import com.microsoft.semantickernel.exceptions.AIException.ErrorCodes;
import com.microsoft.semantickernel.exceptions.SKCheckedException;
import com.microsoft.semantickernel.exceptions.SKException;
import com.microsoft.semantickernel.hooks.KernelHookEvent;
import com.microsoft.semantickernel.hooks.KernelHooks;
import com.microsoft.semantickernel.hooks.PostChatCompletionEvent;
import com.microsoft.semantickernel.hooks.PreChatCompletionEvent;
import com.microsoft.semantickernel.hooks.PreToolCallEvent;
import com.microsoft.semantickernel.implementation.CollectionUtil;
import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.orchestration.FunctionResultMetadata;
import com.microsoft.semantickernel.orchestration.InvocationContext;
import com.microsoft.semantickernel.orchestration.InvocationReturnMode;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.orchestration.ToolCallBehavior;
import com.microsoft.semantickernel.semanticfunctions.KernelFunction;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionArguments;
import com.microsoft.semantickernel.services.chatcompletion.AuthorRole;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.services.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.services.chatcompletion.ChatMessageContent;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;
import java.util.stream.Stream;
import javax.annotation.CheckReturnValue;
import javax.annotation.Nullable;

import com.microsoft.semantickernel.services.openai.OpenAiServiceBuilder;
import org.apache.commons.text.StringEscapeUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * OpenAI chat completion service.
 */
public class OpenAIChatCompletion extends OpenAiService implements ChatCompletionService {

    private static final Logger LOGGER = LoggerFactory.getLogger(OpenAIChatCompletion.class);

    protected OpenAIChatCompletion(
        OpenAIAsyncClient client,
        String deploymentName,
        String modelId,
        @Nullable String serviceId) {
        super(client, serviceId, modelId, deploymentName);
    }

    /**
     * Create a new instance of {@link OpenAIChatCompletion.Builder}.
     *
     * @return a new instance of {@link OpenAIChatCompletion.Builder}
     */
    public static OpenAIChatCompletion.Builder builder() {
        return new OpenAIChatCompletion.Builder();
    }

    @Override
    public Mono<List<ChatMessageContent<?>>> getChatMessageContentsAsync(
        ChatHistory chatHistory,
        @Nullable Kernel kernel,
        @Nullable InvocationContext invocationContext) {

        List<ChatRequestMessage> chatRequestMessages = getChatRequestMessages(chatHistory);

        ChatMessages messages = new ChatMessages(chatRequestMessages);

        return internalChatMessageContentsAsync(
            messages,
            kernel,
            invocationContext)
            .flatMap(history -> {
                try {
                    ChatHistory chatHistoryResult;

                    if (invocationContext != null
                        && invocationContext.returnMode() == InvocationReturnMode.FULL_HISTORY) {
                        chatHistoryResult = new ChatHistory(chatHistory.getMessages());
                    } else {
                        chatHistoryResult = new ChatHistory();
                    }

                    chatHistoryResult.addAll(
                        new ChatHistory(toOpenAIChatMessageContent(history.newMessages)));
                    chatHistoryResult.addAll(new ChatHistory(history.newChatMessageContent));

                    if (invocationContext != null
                        && invocationContext
                            .returnMode() == InvocationReturnMode.LAST_MESSAGE_ONLY) {
                        chatHistoryResult = new ChatHistory(
                            Collections.singletonList(
                                CollectionUtil.getLastOrNull(chatHistory.getMessages())));
                    }

                    return Mono.just(chatHistoryResult.getMessages());
                } catch (Exception e) {
                    return Mono.error(e);
                }
            });
    }

    @Override
    public Mono<List<ChatMessageContent<?>>> getChatMessageContentsAsync(
        String prompt,
        @Nullable Kernel kernel,
        @Nullable InvocationContext invocationContext) {
        ParsedPrompt parsedPrompt = OpenAiXMLPromptParser.parse(prompt);

        ChatMessages messages = new ChatMessages(parsedPrompt.getChatRequestMessages());

        return internalChatMessageContentsAsync(
            messages,
            kernel,
            invocationContext)
            .flatMap(m -> {
                try {
                    ChatHistory result = new ChatHistory(toOpenAIChatMessageContent(m.allMessages));

                    result.addAll(new ChatHistory(m.newChatMessageContent));

                    if (invocationContext != null
                        && invocationContext
                            .returnMode() == InvocationReturnMode.LAST_MESSAGE_ONLY) {
                        result = new ChatHistory(
                            Collections.singletonList(
                                CollectionUtil.getLastOrNull(result.getMessages())));
                    }

                    return Mono.just(result.getMessages());
                } catch (SKCheckedException e) {
                    return Mono.error(e);
                }
            });
    }

    // Holds messages temporarily as we build up our result
    private static class ChatMessages {

        private final List<ChatRequestMessage> newMessages;
        private final List<ChatRequestMessage> allMessages;
        private final List<OpenAIChatMessageContent> newChatMessageContent;

        public ChatMessages(List<ChatRequestMessage> allMessages) {
            this.allMessages = Collections.unmodifiableList(allMessages);
            this.newMessages = Collections.unmodifiableList(new ArrayList<>());
            this.newChatMessageContent = Collections.unmodifiableList(new ArrayList<>());
        }

        private ChatMessages(
            List<ChatRequestMessage> allMessages,
            List<ChatRequestMessage> newMessages,
            List<OpenAIChatMessageContent> newChatMessageContent) {
            this.allMessages = Collections.unmodifiableList(allMessages);
            this.newMessages = Collections.unmodifiableList(newMessages);
            this.newChatMessageContent = Collections.unmodifiableList(newChatMessageContent);
        }

        @CheckReturnValue
        public ChatMessages addAll(List<ChatRequestMessage> requestMessage) {
            List<ChatRequestMessage> tmpAllMessages = new ArrayList<>(allMessages);
            List<ChatRequestMessage> tmpNewMessages = new ArrayList<>(newMessages);
            tmpAllMessages.addAll(requestMessage);
            tmpNewMessages.addAll(requestMessage);
            return new ChatMessages(
                tmpAllMessages,
                tmpNewMessages,
                newChatMessageContent);
        }

        @CheckReturnValue
        public ChatMessages add(ChatRequestMessage requestMessage) {
            return addAll(Arrays.asList(requestMessage));
        }

        @CheckReturnValue
        public ChatMessages addChatMessage(List<OpenAIChatMessageContent> chatMessageContent) {
            ArrayList<OpenAIChatMessageContent> tmpChatMessageContent = new ArrayList<>(
                newChatMessageContent);
            tmpChatMessageContent.addAll(chatMessageContent);

            return new ChatMessages(
                allMessages,
                newMessages,
                tmpChatMessageContent);
        }
    }

    private Mono<ChatMessages> internalChatMessageContentsAsync(
        ChatMessages messages,
        @Nullable Kernel kernel,
        @Nullable InvocationContext invocationContext) {

        List<OpenAIFunction> functions = new ArrayList<>();
        if (kernel != null) {
            kernel.getPlugins()
                .forEach(plugin -> plugin.getFunctions().forEach((name, function) -> functions
                    .add(OpenAIFunction.build(function.getMetadata(), plugin.getName()))));
        }

        // Create copy to avoid reactor exceptions when updating request messages internally
        return internalChatMessageContentsAsync(
            messages,
            kernel,
            functions,
            invocationContext,
            Math.min(MAXIMUM_INFLIGHT_AUTO_INVOKES,
                invocationContext != null && invocationContext.getToolCallBehavior() != null
                    ? invocationContext.getToolCallBehavior().getMaximumAutoInvokeAttempts()
                    : 0));
    }

    private Mono<ChatMessages> internalChatMessageContentsAsync(
        ChatMessages messages,
        @Nullable Kernel kernel,
        List<OpenAIFunction> functions,
        @Nullable InvocationContext invocationContext,
        int autoInvokeAttempts) {

        ChatCompletionsOptions options = executeHook(
            invocationContext,
            new PreChatCompletionEvent(
                getCompletionsOptions(
                    this,
                    messages.allMessages,
                    functions,
                    invocationContext)))
            .getOptions();

        return getClient()
            .getChatCompletionsWithResponse(getDeploymentName(), options,
                OpenAIRequestSettings.getRequestOptions())
            .flatMap(completionsResult -> {
                if (completionsResult.getStatusCode() >= 400) {
                    return Mono.error(new AIException(ErrorCodes.SERVICE_ERROR,
                        "Request failed: " + completionsResult.getStatusCode()));
                }
                return Mono.just(completionsResult.getValue());
            })
            .flatMap(completions -> {
                List<ChatResponseMessage> responseMessages = completions
                    .getChoices()
                    .stream()
                    .map(ChatChoice::getMessage)
                    .filter(Objects::nonNull)
                    .collect(Collectors.toList());

                // execute post chat completion hook
                executeHook(invocationContext, new PostChatCompletionEvent(completions));

                // Just return the result:
                // If we don't want to attempt to invoke any functions
                // Or if we are auto-invoking, but we somehow end up with other than 1 choice even though only 1 was requested
                if (autoInvokeAttempts == 0 || responseMessages.size() != 1) {
                    return getChatMessageContentsAsync(completions)
                        .flatMap(m -> {
                            return Mono.just(messages.addChatMessage(m));
                        });
                }
                // Or if there are no tool calls to be done
                ChatResponseMessage response = responseMessages.get(0);
                List<ChatCompletionsToolCall> toolCalls = response.getToolCalls();
                if (toolCalls == null || toolCalls.isEmpty()) {
                    return getChatMessageContentsAsync(completions)
                        .flatMap(m -> {
                            return Mono.just(messages.addChatMessage(m));
                        });
                }

                ChatRequestAssistantMessage requestMessage = new ChatRequestAssistantMessage(
                    response.getContent());
                requestMessage.setToolCalls(toolCalls);

                // Add the original assistant message to the chat options; this is required for the service
                // to understand the tool call responses
                ChatMessages messagesWithToolCall = messages.add(requestMessage);

                return Flux
                    .fromIterable(toolCalls)
                    .reduce(
                        Mono.just(messagesWithToolCall),
                        (requestMessages, toolCall) -> {
                            if (toolCall instanceof ChatCompletionsFunctionToolCall) {
                                return performToolCall(kernel, invocationContext, requestMessages,
                                    toolCall);
                            }

                            return requestMessages;
                        })
                    .flatMap(it -> it)
                    .flatMap(msgs -> {
                        return internalChatMessageContentsAsync(msgs, kernel, functions,
                            invocationContext, autoInvokeAttempts - 1);
                    })
                    .onErrorResume(e -> {

                        LOGGER.warn("Tool invocation attempt failed: ", e);

                        // If FunctionInvocationError occurred and there are still attempts left, retry, else exit
                        if (autoInvokeAttempts > 0) {
                            ChatMessages currentMessages = messages;
                            if (e instanceof FunctionInvocationError) {
                                currentMessages = currentMessages.addAll(
                                    ((FunctionInvocationError) e).getMessages());
                            }
                            return internalChatMessageContentsAsync(
                                currentMessages,
                                kernel,
                                functions,
                                invocationContext,
                                autoInvokeAttempts - 1);
                        } else {
                            return Mono.error(e);
                        }
                    });
            });
    }

    private Mono<ChatMessages> performToolCall(
        @Nullable Kernel kernel,
        @Nullable InvocationContext invocationContext,
        Mono<ChatMessages> requestMessages,
        ChatCompletionsToolCall toolCall) {

        return requestMessages
            .flatMap(messages -> {
                try {
                    // OpenAI only supports function tool call at the moment
                    ChatCompletionsFunctionToolCall functionToolCall = (ChatCompletionsFunctionToolCall) toolCall;
                    if (kernel == null) {
                        return Mono.error(new SKException(
                            "A tool call was requested, but no kernel was provided to the invocation, this is a unsupported configuration"));
                    }

                    ContextVariableTypes contextVariableTypes = invocationContext == null
                        ? new ContextVariableTypes()
                        : invocationContext.getContextVariableTypes();

                    return invokeFunctionTool(
                        kernel,
                        invocationContext,
                        functionToolCall,
                        contextVariableTypes)
                        .map(functionResult -> {
                            // Add chat request tool message to the chat options
                            ChatRequestMessage requestToolMessage = new ChatRequestToolMessage(
                                functionResult.getResult(),
                                functionToolCall.getId());

                            return messages.add(requestToolMessage);
                        })
                        .switchIfEmpty(Mono.fromSupplier(
                            () -> {
                                ChatRequestMessage requestToolMessage = new ChatRequestToolMessage(
                                    "Completed successfully with no return value",
                                    functionToolCall.getId());

                                return messages.add(requestToolMessage);
                            }))
                        .onErrorResume(e -> emitError(toolCall, messages, e));
                } catch (Exception e) {
                    return emitError(toolCall, messages, e);
                }
            });
    }

    private Mono<ChatMessages> emitError(
        ChatCompletionsToolCall toolCall,
        ChatMessages msgs,
        Throwable e) {
        msgs = msgs.add(new ChatRequestToolMessage(
            "Call failed: " + e.getMessage(),
            toolCall.getId()));

        return Mono.error(new FunctionInvocationError(e, msgs.allMessages));
    }

    /**
     * Exception to be thrown when a function invocation fails.
     */
    private static class FunctionInvocationError extends SKException {

        private final List<ChatRequestMessage> messages;

        public FunctionInvocationError(Throwable e, List<ChatRequestMessage> msgs) {
            super(e.getMessage(), e);
            this.messages = msgs;
        }

        public List<ChatRequestMessage> getMessages() {
            return messages;
        }
    }

    @SuppressWarnings("StringSplitter")
    private Mono<FunctionResult<String>> invokeFunctionTool(
        Kernel kernel,
        @Nullable InvocationContext invocationContext,
        ChatCompletionsFunctionToolCall toolCall,
        ContextVariableTypes contextVariableTypes) {

        try {
            OpenAIFunctionToolCall openAIFunctionToolCall = extractOpenAIFunctionToolCall(toolCall);
            String pluginName = openAIFunctionToolCall.getPluginName();
            if (pluginName == null || pluginName.isEmpty()) {
                return Mono.error(
                    new SKException("Plugin name is required for function tool call"));
            }

            KernelFunction<?> function = kernel.getFunction(
                pluginName,
                openAIFunctionToolCall.getFunctionName());

            PreToolCallEvent hookResult = executeHook(invocationContext, new PreToolCallEvent(
                openAIFunctionToolCall.getFunctionName(),
                openAIFunctionToolCall.getArguments(),
                function,
                contextVariableTypes));

            function = hookResult.getFunction();
            KernelFunctionArguments arguments = hookResult.getArguments();

            return function
                .invokeAsync(kernel)
                .withArguments(arguments)
                .withResultType(contextVariableTypes.getVariableTypeForClass(String.class));
        } catch (JsonProcessingException e) {
            return Mono.error(new SKException("Failed to parse tool arguments", e));
        }
    }

    private static <T extends KernelHookEvent> T executeHook(
        @Nullable InvocationContext invocationContext,
        T event) {
        KernelHooks kernelHooks = invocationContext != null
            && invocationContext.getKernelHooks() != null
                ? invocationContext.getKernelHooks()
                : new KernelHooks();

        return kernelHooks.executeHooks(event);
    }

    @SuppressWarnings("StringSplitter")
    private OpenAIFunctionToolCall extractOpenAIFunctionToolCall(
        ChatCompletionsFunctionToolCall toolCall)
        throws JsonProcessingException {

        // Split the full name of a function into plugin and function name
        String name = toolCall.getFunction().getName();
        String[] parts = name.split(OpenAIFunction.getNameSeparator());
        String pluginName = parts.length > 1 ? parts[0] : "";
        String fnName = parts.length > 1 ? parts[1] : parts[0];

        KernelFunctionArguments arguments = KernelFunctionArguments.builder().build();

        ObjectMapper mapper = new ObjectMapper();
        JsonNode jsonToolCallArguments = mapper.readTree(toolCall.getFunction().getArguments());

        jsonToolCallArguments.fields().forEachRemaining(
            entry -> {
                if (entry.getValue() instanceof ContainerNode) {
                    arguments.put(entry.getKey(),
                        ContextVariable.of(entry.getValue().toPrettyString()));
                } else {
                    arguments.put(entry.getKey(),
                        ContextVariable.of(entry.getValue().asText()));
                }
            });

        return new OpenAIFunctionToolCall(
            toolCall.getId(),
            pluginName,
            fnName,
            arguments);
    }

    private Mono<List<OpenAIChatMessageContent>> getChatMessageContentsAsync(
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
            .flatMap(response -> {
                try {
                    return Mono.just(new OpenAIChatMessageContent(
                        AuthorRole.ASSISTANT,
                        response.getContent(),
                        this.getModelId(),
                        null,
                        null,
                        completionMetadata,
                        formOpenAiToolCalls(response)));
                } catch (Exception e) {
                    return Mono.error(e);
                }
            })
            .collectList();
    }

    private List<ChatMessageContent<?>> toOpenAIChatMessageContent(
        List<ChatRequestMessage> requestMessages) throws SKCheckedException {
        try {
            return requestMessages
                .stream()
                .map(message -> {
                    if (message instanceof ChatRequestUserMessage) {
                        return new OpenAIChatMessageContent<>(
                            AuthorRole.USER,
                            ((ChatRequestUserMessage) message).getContent().toString(),
                            null,
                            null,
                            null,
                            null,
                            null);
                    } else if (message instanceof ChatRequestSystemMessage) {
                        return new OpenAIChatMessageContent<>(
                            AuthorRole.SYSTEM,
                            ((ChatRequestSystemMessage) message).getContent(),
                            null,
                            null,
                            null,
                            null,
                            null);
                    } else if (message instanceof ChatRequestAssistantMessage) {
                        try {
                            List<OpenAIFunctionToolCall> calls = getToolCalls(
                                ((ChatRequestAssistantMessage) message).getToolCalls());
                            return new OpenAIChatMessageContent<>(
                                AuthorRole.ASSISTANT,
                                ((ChatRequestAssistantMessage) message).getContent(),
                                null,
                                null,
                                null,
                                null,
                                calls);
                        } catch (SKCheckedException e) {
                            throw SKException.build("Failed to form assistant message", e);
                        }
                    } else if (message instanceof ChatRequestToolMessage) {
                        return new OpenAIChatMessageContent<>(
                            AuthorRole.TOOL,
                            ((ChatRequestToolMessage) message).getContent(),
                            null,
                            null,
                            null,
                            FunctionResultMetadata.build(
                                ((ChatRequestToolMessage) message).getToolCallId(),
                                null,
                                null),
                            null);
                    }

                    throw new SKException(
                        "Unknown message type: " + message.getClass().getSimpleName());
                })
                .collect(Collectors.toList());
        } catch (SKException e) {
            throw SKCheckedException.build("Failed to form OpenAI chat message content", e);
        }
    }

    @Nullable
    private List<OpenAIFunctionToolCall> getToolCalls(
        @Nullable List<ChatCompletionsToolCall> toolCalls) throws SKCheckedException {
        if (toolCalls == null || toolCalls.isEmpty()) {
            return null;
        }

        try {
            return toolCalls
                .stream()
                .map(call -> {
                    if (call instanceof ChatCompletionsFunctionToolCall) {
                        try {
                            return extractOpenAIFunctionToolCall(
                                (ChatCompletionsFunctionToolCall) call);
                        } catch (JsonProcessingException e) {
                            throw SKException.build("Failed to parse tool arguments", e);
                        }
                    } else {
                        throw new SKException(
                            "Unknown tool call type: " + call.getClass().getSimpleName());
                    }
                })
                .collect(Collectors.toList());
        } catch (SKException e) {
            throw SKCheckedException.build("Failed to form tool call", e);
        }
    }

    @Nullable
    private List<OpenAIFunctionToolCall> formOpenAiToolCalls(
        ChatResponseMessage response) throws SKCheckedException {
        if (response.getToolCalls() == null || response.getToolCalls().isEmpty()) {
            return null;
        }
        try {
            return response
                .getToolCalls()
                .stream()
                .map(call -> {
                    if (call instanceof ChatCompletionsFunctionToolCall) {
                        try {
                            return extractOpenAIFunctionToolCall(
                                (ChatCompletionsFunctionToolCall) call);
                        } catch (JsonProcessingException e) {
                            throw SKException.build("Failed to parse tool arguments", e);
                        }
                    } else {
                        return null;
                    }
                })
                .filter(Objects::nonNull)
                .collect(Collectors.toList());
        } catch (SKException e) {
            throw SKCheckedException.build("Failed to form tool call", e);
        }
    }

    private static ChatCompletionsOptions getCompletionsOptions(
        ChatCompletionService chatCompletionService,
        List<ChatRequestMessage> chatRequestMessages,
        @Nullable List<OpenAIFunction> functions,
        @Nullable InvocationContext invocationContext) {

        chatRequestMessages = chatRequestMessages
            .stream()
            .map(OpenAiXMLPromptParser::unescapeRequest)
            .collect(Collectors.toList());

        ChatCompletionsOptions options = new ChatCompletionsOptions(chatRequestMessages)
            .setModel(chatCompletionService.getModelId());

        if (invocationContext != null && invocationContext.getToolCallBehavior() != null) {
            configureToolCallBehaviorOptions(
                options,
                invocationContext.getToolCallBehavior(),
                functions,
                chatRequestMessages);
        }

        PromptExecutionSettings promptExecutionSettings = invocationContext != null
            ? invocationContext.getPromptExecutionSettings()
            : null;

        if (promptExecutionSettings == null) {
            return options;
        }

        if (promptExecutionSettings.getResultsPerPrompt() < 1
            || promptExecutionSettings.getResultsPerPrompt() > MAX_RESULTS_PER_PROMPT) {
            throw new AIException(AIException.ErrorCodes.INVALID_REQUEST,
                String.format("Results per prompt must be in range between 1 and %d, inclusive.",
                    MAX_RESULTS_PER_PROMPT));
        }

        Map<String, Integer> logit = null;
        if (promptExecutionSettings.getTokenSelectionBiases() != null) {
            logit = promptExecutionSettings
                .getTokenSelectionBiases()
                .entrySet()
                .stream()
                .collect(Collectors.toMap(
                    entry -> entry.getKey().toString(),
                    Map.Entry::getValue));
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

        if (promptExecutionSettings.getResponseFormat() != null) {
            switch (promptExecutionSettings.getResponseFormat()) {
                case JSON_OBJECT:
                    options.setResponseFormat(new ChatCompletionsJsonResponseFormat());
                    break;
                case TEXT:
                    options.setResponseFormat(new ChatCompletionsTextResponseFormat());
                    break;
                default:
                    throw new SKException(
                        "Unknown response format: " + promptExecutionSettings.getResponseFormat());
            }
        }

        return options;
    }

    private static void configureToolCallBehaviorOptions(
        ChatCompletionsOptions options,
        @Nullable ToolCallBehavior toolCallBehavior,
        @Nullable List<OpenAIFunction> functions,
        List<ChatRequestMessage> chatRequestMessages) {

        if (toolCallBehavior == null) {
            return;
        }

        if (functions == null || functions.isEmpty()) {
            return;
        }

        // If a specific function is required to be called
        if (toolCallBehavior instanceof ToolCallBehavior.RequiredKernelFunction) {
            KernelFunction<?> toolChoice = ((ToolCallBehavior.RequiredKernelFunction) toolCallBehavior)
                .getRequiredFunction();

            String toolChoiceName = String.format("%s%s%s",
                toolChoice.getPluginName(),
                OpenAIFunction.getNameSeparator(),
                toolChoice.getName());

            // If required tool call has already been called dont ask for it again
            boolean hasBeenExecuted = hasToolCallBeenExecuted(chatRequestMessages, toolChoiceName);
            if (hasBeenExecuted) {
                return;
            }

            List<ChatCompletionsToolDefinition> toolDefinitions = new ArrayList<>();

            toolDefinitions.add(new ChatCompletionsFunctionToolDefinition(
                OpenAIFunction.toFunctionDefinition(
                    toolChoice.getMetadata(),
                    toolChoice.getPluginName())));

            options.setTools(toolDefinitions);
            try {
                String json = String.format(
                    "{\"type\":\"function\",\"function\":{\"name\":\"%s\"}}", toolChoiceName);
                options.setToolChoice(BinaryData.fromObject(new ObjectMapper().readTree(json)));
            } catch (JsonProcessingException e) {
                throw SKException.build("Failed to parse tool choice", e);
            }
            return;
        }

        // If a set of functions are enabled to be called
        ToolCallBehavior.AllowedKernelFunctions enabledKernelFunctions = (ToolCallBehavior.AllowedKernelFunctions) toolCallBehavior;
        List<ChatCompletionsToolDefinition> toolDefinitions = functions.stream()
            .filter(function -> {
                // check if all kernel functions are enabled
                if (enabledKernelFunctions.isAllKernelFunctionsAllowed()) {
                    return true;
                }
                // otherwise, check for the specific function
                return enabledKernelFunctions.isFunctionAllowed(function.getPluginName(),
                    function.getName());
            })
            .map(OpenAIFunction::getFunctionDefinition)
            .map(ChatCompletionsFunctionToolDefinition::new)
            .collect(Collectors.toList());

        if (toolDefinitions.isEmpty()) {
            return;
        }

        options.setTools(toolDefinitions);
        options.setToolChoice(BinaryData.fromString("auto"));
    }

    private static boolean hasToolCallBeenExecuted(List<ChatRequestMessage> chatRequestMessages,
        String toolChoiceName) {
        return chatRequestMessages
            .stream()
            .flatMap(message -> {
                // Extract tool calls
                if (message instanceof ChatRequestAssistantMessage) {
                    return ((ChatRequestAssistantMessage) message).getToolCalls().stream();
                }
                return Stream.empty();
            })
            .filter(toolCall -> {
                // Filter if tool call has correct name
                if (toolCall instanceof ChatCompletionsFunctionToolCall) {
                    return ((ChatCompletionsFunctionToolCall) toolCall).getFunction().getName()
                        .equals(toolChoiceName);
                }
                return false;
            })
            .allMatch(toolcall -> {
                String id = toolcall.getId();
                // True if tool call id has a response message
                return chatRequestMessages
                    .stream()
                    .filter(
                        chatRequestMessage -> chatRequestMessage instanceof ChatRequestToolMessage)
                    .anyMatch(
                        chatRequestMessage -> ((ChatRequestToolMessage) chatRequestMessage)
                            .getToolCallId()
                            .equals(id));
            });
    }

    private static List<ChatRequestMessage> getChatRequestMessages(
        List<? extends ChatMessageContent> messages) {
        if (messages == null || messages.isEmpty()) {
            return new ArrayList<>();
        }
        return messages.stream()
            .map(OpenAIChatCompletion::getChatRequestMessage)
            .collect(Collectors.toList());
    }

    private static List<ChatRequestMessage> getChatRequestMessages(ChatHistory chatHistory) {
        return getChatRequestMessages(chatHistory.getMessages());
    }

    private static ChatRequestMessage getChatRequestMessage(
        ChatMessageContent<?> message) {

        AuthorRole authorRole = message.getAuthorRole();
        String content = message.getContent();

        switch (authorRole) {
            case ASSISTANT:
                return formAssistantMessage(message, content);
            case SYSTEM:
                return new ChatRequestSystemMessage(content);
            case USER:
                return new ChatRequestUserMessage(content);
            case TOOL:
                String id = null;

                if (message.getMetadata() != null) {
                    id = message.getMetadata().getId();
                }

                if (id == null) {
                    throw new SKException(
                        "Require to create a tool call message, but no tool call id is available");
                }
                return new ChatRequestToolMessage(content, id);
            default:
                LOGGER.debug("Unexpected author role: {}", authorRole);
                throw new SKException("Unexpected author role: " + authorRole);
        }

    }

    private static ChatRequestAssistantMessage formAssistantMessage(
        ChatMessageContent<?> message,
        @Nullable String content) {
        // TODO: handle tools other than function calls
        ChatRequestAssistantMessage asstMessage = new ChatRequestAssistantMessage(content);

        List<OpenAIFunctionToolCall> toolCalls = null;
        if (message instanceof OpenAIChatMessageContent) {
            toolCalls = ((OpenAIChatMessageContent<?>) message).getToolCall();
        }

        if (toolCalls != null) {
            asstMessage.setToolCalls(
                toolCalls.stream()
                    .map(toolCall -> {
                        KernelFunctionArguments arguments = toolCall.getArguments();

                        String args = arguments != null && !arguments.isEmpty()
                            ? arguments.entrySet().stream()
                                .map(entry -> String.format("\"%s\": \"%s\"",
                                    StringEscapeUtils.escapeJson(entry.getKey()),
                                    StringEscapeUtils.escapeJson(
                                        entry.getValue().toPromptString())))
                                .collect(Collectors.joining(",", "{", "}"))
                            : "{}";

                        String prefix = "";
                        if (toolCall.getPluginName() != null) {
                            prefix = toolCall.getPluginName() + OpenAIFunction.getNameSeparator();
                        }
                        String name = prefix + toolCall.getFunctionName();

                        FunctionCall fnCall = new FunctionCall(name, args);
                        return new ChatCompletionsFunctionToolCall(toolCall.getId(),
                            fnCall);
                    })
                    .collect(Collectors.toList()));
        }
        return asstMessage;
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
                throw new SKException("Unexpected author role: " + authorRole);
        }

    }

    /**
     * Builder for creating a new instance of {@link OpenAIChatCompletion}.
     */
    public static class Builder extends OpenAiServiceBuilder<OpenAIChatCompletion, Builder> {

        @Override
        public OpenAIChatCompletion build() {

            if (this.client == null) {
                throw new AIException(AIException.ErrorCodes.INVALID_REQUEST,
                    "OpenAI client must be provided");
            }

            if (this.modelId == null || modelId.isEmpty()) {
                throw new AIException(AIException.ErrorCodes.INVALID_REQUEST,
                    "OpenAI model id must be provided");
            }

            if (deploymentName == null) {
                LOGGER.debug("Deployment name is not provided, using model id as deployment name");
                deploymentName = modelId;
            }

            return new OpenAIChatCompletion(client, deploymentName, modelId, serviceId);
        }
    }
}
