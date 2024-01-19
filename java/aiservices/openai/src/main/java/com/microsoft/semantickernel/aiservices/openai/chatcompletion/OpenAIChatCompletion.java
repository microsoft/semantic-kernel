package com.microsoft.semantickernel.aiservices.openai.chatcompletion;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.models.ChatChoice;
import com.azure.ai.openai.models.ChatCompletions;
import com.azure.ai.openai.models.ChatCompletionsFunctionToolCall;
import com.azure.ai.openai.models.ChatCompletionsFunctionToolDefinition;
import com.azure.ai.openai.models.ChatCompletionsOptions;
import com.azure.ai.openai.models.ChatCompletionsToolCall;
import com.azure.ai.openai.models.ChatRequestAssistantMessage;
import com.azure.ai.openai.models.ChatRequestMessage;
import com.azure.ai.openai.models.ChatRequestSystemMessage;
import com.azure.ai.openai.models.ChatRequestToolMessage;
import com.azure.ai.openai.models.ChatRequestUserMessage;
import com.azure.ai.openai.models.ChatResponseMessage;
import com.azure.ai.openai.models.FunctionCall;
import com.azure.ai.openai.models.FunctionDefinition;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.chatcompletion.AuthorRole;
import com.microsoft.semantickernel.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.chatcompletion.ChatMessageContent;
import com.microsoft.semantickernel.chatcompletion.StreamingChatMessageContent;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableType;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;
import javax.annotation.Nullable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
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

    public static OpenAIChatCompletion.Builder builder() {
        return new OpenAIChatCompletion.Builder();
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
        List<FunctionDefinition> functions = Collections.emptyList();
        return internalChatMessageContentsAsync(chatRequestMessages, functions,
            promptExecutionSettings);

    }

    @Override
    public Mono<List<ChatMessageContent>> getChatMessageContentsAsync(String prompt,
        PromptExecutionSettings promptExecutionSettings, Kernel kernel) {
        ParsedPrompt parsedPrompt = XMLPromptParser.parse(prompt);
        return internalChatMessageContentsAsync(
            parsedPrompt.getChatRequestMessages(),
            parsedPrompt.getFunctions(),
            promptExecutionSettings);
    }

    private Mono<List<ChatMessageContent>> internalChatMessageContentsAsync(
        List<ChatRequestMessage> chatRequestMessages,
        List<FunctionDefinition> functions,
        PromptExecutionSettings promptExecutionSettings) {
        ChatCompletionsOptions options = getCompletionsOptions(this, chatRequestMessages, functions,
            promptExecutionSettings);
        Mono<List<ChatMessageContent>> results =
            internalChatMessageContentsAsync(options);

        return results.flatMap(list -> {
            boolean makeSecondCall = false;
            for (ChatMessageContent messageContent : list) {
                if (messageContent.getAuthorRole() == AuthorRole.TOOL) {
                    makeSecondCall = true;
                    String content = messageContent.getContent();
                    String id = messageContent.getModelId();
                    ChatRequestToolMessage toolMessage = new ChatRequestToolMessage(content, id);
                    chatRequestMessages.add(toolMessage);
                }
            }
            if (makeSecondCall) {
                return internalChatMessageContentsAsync(options);
            }
            return Mono.just(list);
        });
    }

    private Mono<List<ChatMessageContent>> internalChatMessageContentsAsync(
        ChatCompletionsOptions options) {

        return client
            .getChatCompletions(getModelId(), options)
            .mapNotNull(ChatCompletions::getChoices)
            .filter(choices -> choices != null && !choices.isEmpty())
            .map(this::accumulateResponses)
            .map(responses ->
                responses.stream()
                    .map(ChatResponseCollector::toChatMessageContent)
                    .collect(Collectors.toList())
            );

    }


    // non-streaming case
    private List<ChatResponseCollector> accumulateResponses(List<ChatChoice> choices) {
        List<ChatResponseCollector> collectors = new ArrayList<>();
        choices.stream()
            .map(ChatChoice::getMessage)
            .filter(Objects::nonNull)
            .map(this::accumulateResponse)
            .forEach(collectors::add);
        return collectors;
    }


    private ChatResponseCollector accumulateResponse(ChatResponseMessage response) {
        ChatResponseCollector collector = new ChatResponseCollector();

        // collector is null for the non-streaming case and not null for the streaming case
        if (response.getContent() != null) {
            collector.append(AuthorRole.ASSISTANT, response.getContent());
        } else if (response.getToolCalls() != null) {
            List<ChatCompletionsToolCall> toolCalls = response.getToolCalls();
            // TODO: This assumes one tool call per response, which is _definitely_ a bad assumption.
            for (ChatCompletionsToolCall toolCall : toolCalls) {
                if (toolCall instanceof ChatCompletionsFunctionToolCall) {
                    collector.append(AuthorRole.TOOL, (ChatCompletionsFunctionToolCall) toolCall);
                }
            }
        }
        return collector;
    }

    /*
     * Given a json string, invoke the tool specified in the json string.
     * At this time, the only tool we have is 'function'.
     * The json string should be of the form:
     * {"type":"function", "function": {"name":"search-search", "parameters": {"query":"Banksy"}}}
     * where 'name' is <plugin name '-' function name>.
     */
    private Mono<StreamingChatMessageContent> invokeTool(Kernel kernel, String json) {
        try {
            ObjectMapper mapper = new ObjectMapper();
            JsonNode jsonNode = mapper.readTree(json);
            String id = jsonNode.get("id").asText("");
            jsonNode = jsonNode.get("function");
            if (jsonNode != null) {
                // function is the only tool we have right now.
                Mono<ContextVariable<String>> result = invokeFunction(kernel, jsonNode);
                if (result != null) {
                    return result.map(contextVariable -> {
                        String content = contextVariable.getValue();
                        return new StreamingChatMessageContent(AuthorRole.TOOL, content).setModelId(
                            id);
                    });
                }
            }
        } catch (JsonProcessingException e) {
            LOGGER.error("Failed to parse json", e);
        }
        return Mono.empty();
    }

    /*
     * The jsonNode should represent: {"name":"search-search", "parameters": {"query":"Banksy"}}}
     */
    private Mono<ContextVariable<String>> invokeFunction(Kernel kernel, JsonNode jsonNode) {
        String name = jsonNode.get("name").asText();
        String[] parts = name.split("-");
        String pluginName = parts.length > 0 ? parts[0] : "";
        String fnName = parts.length > 1 ? parts[1] : "";
        JsonNode parameters = jsonNode.get("parameters");
        KernelFunction kernelFunction = kernel.getPlugins().getFunction(pluginName, fnName);
        if (kernelFunction == null) {
            return Mono.empty();
        }

        KernelArguments arguments = null;
        if (parameters != null) {
            Map<String, ContextVariable<?>> variables = new HashMap<>();
            parameters.fields().forEachRemaining(entry -> {
                String paramName = entry.getKey();
                String paramValue = entry.getValue().asText();
                ContextVariable<?> contextVariable = ContextVariable.of(paramValue);
                variables.put(paramName, contextVariable);
            });
            arguments = KernelArguments.builder().withVariables(variables).build();
        }
        ContextVariableType<String> variableType = ContextVariableTypes.getDefaultVariableTypeForClass(
            String.class);
        return kernelFunction.invokeAsync(kernel, arguments, variableType);
    }

    private static ChatCompletionsOptions getCompletionsOptions(
        ChatCompletionService chatCompletionService,
        List<ChatRequestMessage> chatRequestMessages,
        List<FunctionDefinition> functions,
        PromptExecutionSettings promptExecutionSettings) {
        ChatCompletionsOptions options = new ChatCompletionsOptions(chatRequestMessages)
            .setModel(chatCompletionService.getModelId());

        if (functions != null && !functions.isEmpty()) {
            // options.setFunctions(functions);
            options.setTools(
                functions.stream()
                    .map(ChatCompletionsFunctionToolDefinition::new)
                    .collect(Collectors.toList())
            );
        }

        if (promptExecutionSettings == null) {
            return options;
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

    private interface ContentBuffer<T> {

        void append(T content);

        ChatMessageContent toChatMessageContent();
    }

    private static class AssistantContentBuffer implements ContentBuffer<String> {

        private final StringBuilder sb = new StringBuilder();

        @Override
        public void append(String content) {
            sb.append(content);
        }

        @Override
        public ChatMessageContent toChatMessageContent() {
            return new ChatMessageContent(AuthorRole.ASSISTANT, sb.toString());
        }
    }

    private static class ToolContentBuffer implements
        ContentBuffer<ChatCompletionsFunctionToolCall> {

        private String id = null;
        private String name = null;
        private List<String> arguments = new ArrayList<>();

        @Override
        public void append(ChatCompletionsFunctionToolCall toolCall) {
            FunctionCall function = toolCall.getFunction();
            String toolCallId = toolCall.getId();
            String fnName = function.getName();
            String fnArguments = function.getArguments();
            if (this.id == null && toolCallId != null && !toolCallId.isEmpty()) {
                this.id = toolCallId;
            }
            if (this.name == null && fnName != null && !fnName.isEmpty()) {
                this.name = fnName;
            }
            if (fnArguments != null && !fnArguments.isEmpty()) {
                this.arguments.add(fnArguments);
            }
        }

        @Override
        public ChatMessageContent toChatMessageContent() {
            return new ChatMessageContent(AuthorRole.TOOL, toJsonString());
        }

        private String toJsonString() {
            StringBuilder sb = new StringBuilder(
                String.format("{\"type\":\"function\", \"id\":\"%s\", \"function\": ", id));
            sb.append(String.format("{\"name\":\"%s\", \"parameters\": ", name));
            // when concatentated, args should be valid json
            for (String argument : arguments) {
                sb.append(argument);
            }
            // close off function, and type
            sb.append("}}");
            assert isBalanced(sb.toString());
            return sb.toString();
        }

        // used to check that the json string is balanced
        private boolean isBalanced(String str) {
            int openParens = 0;
            int closeParens = 0;
            boolean inString = false;
            for (int i = 0; i < str.length(); i++) {
                char c = str.charAt(i);
                if (!inString && c == '(') {
                    openParens++;
                } else if (!inString && c == ')') {
                    closeParens++;
                } else if (c == '"') {
                    inString = !inString;
                }
            }
            return openParens == closeParens;
        }
    }

    // For streaming,
    private static class ChatResponseCollector {

        private final Map<AuthorRole, ContentBuffer<?>> roleToContent = new HashMap<>();

        private ContentBuffer<?> collectorFor(AuthorRole role) {
            return roleToContent.computeIfAbsent(role, k -> {
                if (k == AuthorRole.TOOL) {
                    return new ToolContentBuffer();
                }
                return new AssistantContentBuffer();
            });
        }

        @SuppressWarnings("unchecked")
        private <T> void append(AuthorRole role, T content) {
            ContentBuffer<T> contentBuffer = (ContentBuffer<T>) collectorFor(role);
            contentBuffer.append(content);
        }

        private ChatMessageContent toChatMessageContent() {
            assert roleToContent.size() == 1;
            ContentBuffer<?> contentBuffer = roleToContent.values().iterator().next();
            return contentBuffer.toChatMessageContent();
        }
    }


    public static class Builder extends ChatCompletionService.Builder {

        @Override
        public OpenAIChatCompletion build() {
            return new OpenAIChatCompletion(client, modelId, serviceId);
        }
    }
}
