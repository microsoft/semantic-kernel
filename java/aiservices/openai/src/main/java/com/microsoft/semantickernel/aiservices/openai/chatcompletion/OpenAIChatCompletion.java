package com.microsoft.semantickernel.aiservices.openai.chatcompletion;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

import javax.annotation.Nullable;
import javax.xml.namespace.QName;
import javax.xml.stream.XMLEventReader;
import javax.xml.stream.XMLInputFactory;
import javax.xml.stream.XMLStreamException;
import javax.xml.stream.events.Attribute;
import javax.xml.stream.events.StartElement;
import javax.xml.stream.events.XMLEvent;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

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
import com.azure.core.credential.TokenCredential;
import com.azure.core.util.BinaryData;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.chatcompletion.AuthorRole;
import com.microsoft.semantickernel.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.chatcompletion.ChatMessageContent;
import com.microsoft.semantickernel.chatcompletion.StreamingChatMessageContent;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;

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

    @Override
    public Map<String, ContextVariable<?>> getAttributes() {
        return attributes;
    }

    @Override
    public Mono<List<ChatMessageContent>> getChatMessageContentsAsync(ChatHistory chatHistory,
            @Nullable PromptExecutionSettings promptExecutionSettings, @Nullable Kernel kernel) {

        List<ChatRequestMessage> chatRequestMessages = getChatRequestMessages(chatHistory);
        List<FunctionDefinition> functions = Collections.emptyList();
        return internalChatMessageContentsAsync(chatRequestMessages, functions, promptExecutionSettings);

    }

    @Override
    public Flux<StreamingChatMessageContent> getStreamingChatMessageContentsAsync(ChatHistory chatHistory,
            PromptExecutionSettings promptExecutionSettings, Kernel kernel)
    {
        List<ChatRequestMessage> chatRequestMessages = getChatRequestMessages(chatHistory);
        List<FunctionDefinition> functions = Collections.emptyList();
        return internalStreamingChatMessageContentsAsync(chatRequestMessages, functions, promptExecutionSettings);

    }

    @Override
    public Mono<List<ChatMessageContent>> getChatMessageContentsAsync(String prompt,
            PromptExecutionSettings promptExecutionSettings, Kernel kernel) {
        List<ChatRequestMessage> chatRequestMessages = getChatRequestMessages(prompt);
        List<FunctionDefinition> functions = getFunctionDefinitions(prompt);
        return internalChatMessageContentsAsync(chatRequestMessages, functions, promptExecutionSettings);
    }

    @Override
    public Flux<StreamingChatMessageContent> getStreamingChatMessageContentsAsync(String prompt,
            PromptExecutionSettings promptExecutionSettings, Kernel kernel) {
        List<ChatRequestMessage> chatRequestMessages = getChatRequestMessages(prompt);
        List<FunctionDefinition> functions = getFunctionDefinitions(prompt);
        return internalStreamingChatMessageContentsAsync(chatRequestMessages, functions, promptExecutionSettings);
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
            for(String argument : arguments) {
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

        private final Map<AuthorRole,ContentBuffer<?>> roleToContent = new HashMap<>();

        private ContentBuffer<?> collectorFor(AuthorRole role) {
            return roleToContent.computeIfAbsent(role, k -> {
                if (k == AuthorRole.TOOL) return new ToolContentBuffer();
                return new AssistantContentBuffer();
            });
        }

        @SuppressWarnings("unchecked")
        private <T> void append(AuthorRole role, T content) {
            ContentBuffer<T> contentBuffer = (ContentBuffer<T>)collectorFor(role);
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
        PromptExecutionSettings promptExecutionSettings)
    {
        ChatCompletionsOptions options = getCompletionsOptions(this, chatRequestMessages, functions,  promptExecutionSettings);
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
                            accumulator.append(AuthorRole.ASSISTANT, chatResponseMessage.getContent());
                        } else if (chatResponseMessage.getToolCalls() != null) {
                            List<ChatCompletionsToolCall> toolCalls = chatResponseMessage.getToolCalls();
                            toolCalls.forEach(toolCall -> {
                                if (toolCall instanceof ChatCompletionsFunctionToolCall) {
                                    FunctionCall functionCall = ((ChatCompletionsFunctionToolCall)toolCall).getFunction();
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
        PromptExecutionSettings promptExecutionSettings)
    {
        ChatCompletionsOptions options = getCompletionsOptions(this, chatRequestMessages, functions, promptExecutionSettings);
        return client
            .getChatCompletions(getModelId(), options)
            .flatMap(chatCompletions -> Mono.just(toChatMessageContents(chatCompletions)));
    }

    private static ChatCompletionsOptions getCompletionsOptions(
        ChatCompletionService chatCompletionService,
        List<ChatRequestMessage> chatRequestMessages,
        List<FunctionDefinition> functions,
        PromptExecutionSettings promptExecutionSettings)
    {
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
            .setStop(promptExecutionSettings.getStopSequences() == null || promptExecutionSettings.getStopSequences().isEmpty() ? null : promptExecutionSettings.getStopSequences())
            .setUser(promptExecutionSettings.getUser())
            .setLogitBias(new HashMap<>());

        return options;
    }

    private static List<ChatRequestMessage> getChatRequestMessages(ChatHistory chatHistory)
    {
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

    private static List<ChatRequestMessage> getChatRequestMessages(String prompt)
    {
        // TODO: XML parsing should be done as a chain of XMLEvent handlers.
        // If one handler does not recognize the element, it should pass it to the next handler.
        // In this way, we can avoid parsing the whole prompt twice and easily extend the parsing logic.
        List<ChatRequestMessage> messages = new ArrayList<>();
        try (InputStream is = new ByteArrayInputStream(prompt.getBytes())) {
            XMLInputFactory factory = XMLInputFactory.newFactory();
            XMLEventReader reader = factory.createXMLEventReader(is);
            while(reader.hasNext()) {
                XMLEvent event = reader.nextEvent();
                if (event.isStartElement()) {
                    String name = getElementName(event);
                    if (name.equals("message")) {
                        String role = getAttributeValue(event, "role");
                        String content = reader.getElementText();
                        messages.add(getChatRequestMessage(role, content));
                    }
                }
            }
        } catch (IOException | XMLStreamException | IllegalArgumentException e) {
            LOGGER.error("Error parsing prompt", e);
        }
        return messages;
    }

    private static List<FunctionDefinition> getFunctionDefinitions(String prompt)
    {
        // TODO: XML parsing should be done as a chain of XMLEvent handlers. See previous remark.
        // <function pluginName=\"%s\" name=\"%s\"  description=\"%s\">
        //      <parameter name=\"%s\" description=\"%s\" defaultValue=\"%s\" isRequired=\"%s\" type=\"%s\"/>...
        // </function>
        List<FunctionDefinition> functionDefinitions = new ArrayList<>();
        try (InputStream is = new ByteArrayInputStream(prompt.getBytes())) {
            XMLInputFactory factory = XMLInputFactory.newFactory();
            XMLEventReader reader = factory.createXMLEventReader(is);
            FunctionDefinition functionDefinition = null;
            Map<String, String> parameters = new HashMap<>();
            List<String> requiredParmeters = new ArrayList<>();
            while(reader.hasNext()) {
                XMLEvent event = reader.nextEvent();
                if (event.isStartElement()) {
                    String elementName = getElementName(event);
                    if (elementName.equals("function")) {
                        assert functionDefinition == null;
                        assert parameters.isEmpty();
                        assert requiredParmeters.isEmpty();
                        String pluginName = getAttributeValue(event, "pluginName");
                        String name = getAttributeValue(event, "name");
                        String description = getAttributeValue(event, "description");
                        // name has to match '^[a-zA-Z0-9_-]{1,64}$'
                        functionDefinition = new FunctionDefinition(pluginName + "-" +name)
                            .setDescription(description);
                    } else if (elementName.equals("parameter")) {
                        String name = getAttributeValue(event, "name");
                        String type = getAttributeValue(event, "type").toLowerCase(Locale.ROOT);
                        String description = getAttributeValue(event, "description");
                        parameters.put(name, String.format("{\"type\": \"%s\", \"description\": \"%s\"}", "string", description));

                        String isRequired = getAttributeValue(event, "isRequired");
                        if (Boolean.parseBoolean(isRequired)) {
                            requiredParmeters.add(name);
                        }
                    }
                } else if (event.isEndElement()) {
                    String elementName = getElementName(event);
                    if (elementName.equals("function")) {
                        // Example JSON Schema:
                        // {
                        //    "type": "function",
                        //    "function": {
                        //        "name": "get_current_weather",
                        //        "description": "Get the current weather in a given location",
                        //        "parameters": {
                        //            "type": "object",
                        //            "properties": {
                        //                "location": {
                        //                    "type": "string",
                        //                    "description": "The city and state, e.g. San Francisco, CA",
                        //                },
                        //               "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                        //            },
                        //            "required": ["location"],
                        //        },
                        //    },
                        //}
                        assert functionDefinition != null;
                        if (!parameters.isEmpty()) {
                            StringBuilder sb = new StringBuilder("{\"type\": \"object\", \"properties\": {");
                            parameters.forEach((name, value) -> {
                                // make "param": {"type": "string", "description": "desc"},
                                sb.append(String.format("\"%s\": %s,", name, value));
                            });
                            // strip off trailing comma and close the properties object
                            sb.replace(sb.length() - 1, sb.length(), "}");
                            if (!requiredParmeters.isEmpty()) {
                                sb.append(", \"required\": [");
                                requiredParmeters.forEach(name -> {
                                    sb.append(String.format("\"%s\",", name));
                                });
                                // strip off trailing comma and close the required array
                                sb.replace(sb.length() - 1, sb.length(), "]");
                            }
                            // close the object
                            sb.append("}");
                            //System.out.println(sb.toString());
                            ObjectMapper objectMapper = new ObjectMapper();
                            JsonNode jsonNode = objectMapper.readTree(sb.toString());
                            BinaryData binaryData = BinaryData.fromObject(jsonNode);
                            functionDefinition.setParameters(binaryData);
                        }
                        functionDefinitions.add(functionDefinition);
                        functionDefinition = null;
                        parameters.clear();
                        requiredParmeters.clear();
                    }
                }
            }
        } catch (IOException | XMLStreamException | IllegalArgumentException e) {
            LOGGER.error("Error parsing prompt", e);
        }
        return functionDefinitions;
    }

    private static String getElementName(XMLEvent xmlEvent) {
        if (xmlEvent.isStartElement()) {
            return xmlEvent.asStartElement().getName().getLocalPart();
        } else if (xmlEvent.isEndElement()) {
            return xmlEvent.asEndElement().getName().getLocalPart();
        }
        // TODO: programmer's error - log at debug
        return "";
    }

    private static String getAttributeValue(XMLEvent xmlEvent, String attributeName)
    {
        if (xmlEvent.isStartElement()) {
            StartElement element = xmlEvent.asStartElement();
            Attribute attribute = element.getAttributeByName(QName.valueOf(attributeName));
            return attribute != null ? attribute.getValue() : "";
        }
        // TODO: programmer's error - log at debug
        return "";
    }
   
    private static ChatRequestMessage getChatRequestMessage(
        String role,
        String content)
    {
        try {
            AuthorRole authorRole = AuthorRole.valueOf(role.toUpperCase());
            return getChatRequestMessage(authorRole, content);
        } catch (IllegalArgumentException e) {
            LOGGER.debug("Unknown author role: " + role);
            return null;
        }
    }

    private static ChatRequestMessage getChatRequestMessage(
        AuthorRole authorRole,
        String content) {

        switch(authorRole) {
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

        if (chatCompletions == null || chatCompletions.getChoices() == null || chatCompletions.getChoices().isEmpty()) {
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
        if(chatRole == ChatRole.ASSISTANT) {
            return AuthorRole.ASSISTANT;
        }
        if(chatRole == ChatRole.SYSTEM) {
            return AuthorRole.SYSTEM;
        }
        if(chatRole == ChatRole.USER) {
            return AuthorRole.USER;
        }
        if(chatRole == ChatRole.TOOL) {
            return AuthorRole.TOOL;
        }
        throw new IllegalArgumentException("Unknown chat role: " + chatRole);
    }

    public static class Builder implements ChatCompletionService.Builder {
        private OpenAIAsyncClient client;
        private String modelId;

        @Override
        public OpenAIChatCompletion build() {
            return new OpenAIChatCompletion(client, modelId);
        }

        @Override
        public Builder withModelId(String modelId) {
            this.modelId = modelId;
            return this;
        }

        @Override
        public Builder withOpenAIAsyncClient(OpenAIAsyncClient openAIClient) {
            this.client = openAIClient;
            return this;
        }
    }
}
