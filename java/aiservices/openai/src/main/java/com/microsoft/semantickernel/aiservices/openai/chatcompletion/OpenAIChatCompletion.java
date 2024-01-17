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
import com.azure.ai.openai.models.ChatRole;
import com.azure.ai.openai.models.FunctionCall;
import com.azure.ai.openai.models.FunctionDefinition;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.chatcompletion.AuthorRole;
import com.microsoft.semantickernel.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.chatcompletion.ChatMessageContent;
import com.microsoft.semantickernel.chatcompletion.StreamingChatMessageContent;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
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

    public OpenAIChatCompletion(OpenAIAsyncClient client, String modelId) {
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
    public Mono<List<ChatMessageContent>> getChatMessageContentsAsync(ChatHistory chatHistory,
        @Nullable PromptExecutionSettings promptExecutionSettings, @Nullable Kernel kernel) {

        List<ChatRequestMessage> chatRequestMessages = getChatRequestMessages(chatHistory);
        List<FunctionDefinition> functions = Collections.emptyList();
        return internalChatMessageContentsAsync(chatRequestMessages, functions,
            promptExecutionSettings);

    }

    @Override
    public Flux<StreamingChatMessageContent> getStreamingChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings promptExecutionSettings, Kernel kernel) {

        return internalStreamingChatMessageContentsAsync(
            getChatRequestMessages(chatHistory),
            Collections.emptyList(),
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

    @Override
    public Flux<StreamingChatMessageContent> getStreamingChatMessageContentsAsync(
        String prompt,
        PromptExecutionSettings promptExecutionSettings,
        Kernel kernel) {

        ParsedPrompt parsedPrompt = XMLPromptParser.parse(prompt);

        return internalStreamingChatMessageContentsAsync(
            parsedPrompt.getChatRequestMessages(),
            parsedPrompt.getFunctions(),
            promptExecutionSettings);
    }

    private interface ContentBuffer<T> {

        void append(T content);

        StreamingChatMessageContent toStreamingChatMessageContent();
    }

    private static class AssistantContentBuffer implements ContentBuffer<String> {

        private final StringBuilder sb = new StringBuilder();

        @Override
        public void append(String content) {
            sb.append(content);
        }

        @Override
        public StreamingChatMessageContent toStreamingChatMessageContent() {
            return new StreamingChatMessageContent(AuthorRole.ASSISTANT, sb.toString());
        }
    }

    private static class ToolContentBuffer implements ContentBuffer<FunctionCall> {

        private String name = null;
        private List<String> arguments = new ArrayList<>();

        @Override
        public void append(FunctionCall functionCall) {
            String fnName = functionCall.getName();
            String fnArguments = functionCall.getArguments();
            if (this.name == null && fnName != null && !fnName.isEmpty()) {
                this.name = fnName;
            } else if (fnArguments != null && !fnArguments.isEmpty()) {
                this.arguments.add(fnArguments);
            }
        }

        @Override
        public StreamingChatMessageContent toStreamingChatMessageContent() {

            StringBuilder sb = new StringBuilder("{\"type\":\"function\", \"function\": ");
            sb.append(String.format("{\"name\":\"%s\", \"parameters\": ", name));
            boolean first = true;
            // when concatentated, args should be valid json
            for (String argument : arguments) {
                sb.append(argument);
            }
            // close off function, and type
            sb.append("}}");
            assert isBalanced(sb.toString());
            return new StreamingChatMessageContent(AuthorRole.TOOL, sb.toString());
        }

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

        private StreamingChatMessageContent toStreamingChatMessageContent() {
            assert roleToContent.size() == 1;
            ContentBuffer<?> contentBuffer = roleToContent.values().iterator().next();
            return contentBuffer.toStreamingChatMessageContent();
        }
    }

    private Flux<StreamingChatMessageContent> internalStreamingChatMessageContentsAsync(
        List<ChatRequestMessage> chatRequestMessages,
        List<FunctionDefinition> functions,
        PromptExecutionSettings promptExecutionSettings) {
        ChatCompletionsOptions options = getCompletionsOptions(this, chatRequestMessages, functions,
            promptExecutionSettings);
        return client
            .getChatCompletionsStream(getModelId(), options)
            .filter(chatCompletion -> chatCompletion != null)
            .map(ChatCompletions::getChoices)
            .filter(choices -> choices != null && !choices.isEmpty())
            .reduceWith(ChatResponseCollector::new, (accumulator, choices) -> {
                choices.stream()
                    .map(choice -> choice.getDelta())
                    .filter(chatResponseMessage -> chatResponseMessage != null)
                    .forEach(chatResponseMessage -> {
                        if (chatResponseMessage.getContent() != null) {
                            accumulator.append(AuthorRole.ASSISTANT,
                                chatResponseMessage.getContent());
                        } else if (chatResponseMessage.getToolCalls() != null) {
                            List<ChatCompletionsToolCall> toolCalls = chatResponseMessage.getToolCalls();
                            toolCalls.forEach(toolCall -> {
                                if (toolCall instanceof ChatCompletionsFunctionToolCall) {
                                    FunctionCall functionCall = ((ChatCompletionsFunctionToolCall) toolCall).getFunction();
                                    accumulator.append(AuthorRole.TOOL, functionCall);
                                }
                            });
                        }
                    });
                return accumulator;
            })
            .map(ChatResponseCollector::toStreamingChatMessageContent)
            .flux();
    }

    private Mono<List<ChatMessageContent>> internalChatMessageContentsAsync(
        List<ChatRequestMessage> chatRequestMessages,
        List<FunctionDefinition> functions,
        PromptExecutionSettings promptExecutionSettings) {
        ChatCompletionsOptions options = getCompletionsOptions(this, chatRequestMessages, functions,
            promptExecutionSettings);
        return client
            .getChatCompletions(getModelId(), options)
            .flatMap(chatCompletions -> Mono.just(toChatMessageContents(chatCompletions)));
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
            .setLogitBias(new HashMap<>());

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

    private static List<ChatMessageContent> toChatMessageContents(ChatCompletions chatCompletions) {

        if (chatCompletions == null || chatCompletions.getChoices() == null
            || chatCompletions.getChoices().isEmpty()) {
            return new ArrayList<>();
        }

        return chatCompletions.getChoices().stream()
            .map(ChatChoice::getMessage)
            .map(OpenAIChatCompletion::toChatMessageContent)
            .collect(Collectors.toList());
    }

    private static ChatMessageContent toChatMessageContent(ChatResponseMessage message) {
        return new ChatMessageContent(toAuthorRole(message.getRole()), message.getContent());
    }

    private static AuthorRole toAuthorRole(ChatRole chatRole) {
        if (chatRole == null) {
            return null;
        }
        if (chatRole == ChatRole.ASSISTANT) {
            return AuthorRole.ASSISTANT;
        }
        if (chatRole == ChatRole.SYSTEM) {
            return AuthorRole.SYSTEM;
        }
        if (chatRole == ChatRole.USER) {
            return AuthorRole.USER;
        }
        if (chatRole == ChatRole.TOOL) {
            return AuthorRole.TOOL;
        }
        throw new IllegalArgumentException("Unknown chat role: " + chatRole);
    }

    public static class Builder extends ChatCompletionService.Builder {
        @Override
        public OpenAIChatCompletion build() {
            return new OpenAIChatCompletion(client, modelId);
        }
    }
}
