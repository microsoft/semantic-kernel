// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.aiservices.openai.chatcompletion;

import com.azure.ai.openai.models.ChatRequestAssistantMessage;
import com.azure.ai.openai.models.ChatRequestFunctionMessage;
import com.azure.ai.openai.models.ChatRequestMessage;
import com.azure.ai.openai.models.ChatRequestSystemMessage;
import com.azure.ai.openai.models.ChatRequestToolMessage;
import com.azure.ai.openai.models.ChatRequestUserMessage;
import com.azure.ai.openai.models.FunctionDefinition;
import com.azure.core.util.BinaryData;
import com.microsoft.semantickernel.exceptions.SKException;
import com.microsoft.semantickernel.services.chatcompletion.AuthorRole;
import com.microsoft.semantickernel.services.chatcompletion.ChatPromptParseVisitor;
import com.microsoft.semantickernel.services.chatcompletion.ChatXMLPromptParser;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;
import java.util.UUID;
import javax.annotation.Nullable;
import org.apache.commons.text.StringEscapeUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

class OpenAiXMLPromptParser {

    private static final Logger LOGGER = LoggerFactory.getLogger(OpenAiXMLPromptParser.class);

    private static class OpenAiChatPromptParseVisitor implements
        ChatPromptParseVisitor<ParsedPrompt> {

        @Nullable
        private ParsedPrompt parsedRaw = null;
        private final List<FunctionDefinition> functionDefinitions = new ArrayList<>();
        private final List<ChatRequestMessage> messages = new ArrayList<>();

        @Override
        public ChatPromptParseVisitor<ParsedPrompt> addMessage(String role,
            String content) {
            messages.add(getChatRequestMessage(role, content));
            return this;
        }

        @Override
        public ChatPromptParseVisitor<ParsedPrompt> addFunction(
            String name,
            @Nullable String description,
            @Nullable BinaryData parameters) {
            FunctionDefinition function = new FunctionDefinition(name);

            if (description != null) {
                function.setDescription(description);
            }

            if (parameters != null) {
                function.setParameters(parameters);
            }

            functionDefinitions.add(function);

            return this;
        }

        @Override
        public boolean areMessagesEmpty() {
            return messages.isEmpty();
        }

        @Override
        public ChatPromptParseVisitor<ParsedPrompt> fromRawPrompt(String rawPrompt) {
            ChatRequestUserMessage message = new ChatRequestUserMessage(rawPrompt);

            if (message.getName() == null) {
                message.setName(UUID.randomUUID().toString());
            }

            this.parsedRaw = new ParsedPrompt(Collections.singletonList(message), null);
            return this;
        }

        @Override
        public ParsedPrompt get() {
            if (parsedRaw != null) {
                return parsedRaw;
            }

            return new ParsedPrompt(messages, functionDefinitions);
        }

        @Override
        public ChatPromptParseVisitor<ParsedPrompt> reset() {
            return new OpenAiChatPromptParseVisitor();
        }
    }

    public static ParsedPrompt parse(String rawPrompt) {
        ChatPromptParseVisitor<ParsedPrompt> visitor = ChatXMLPromptParser.parse(rawPrompt,
            new OpenAiChatPromptParseVisitor());

        return visitor.get();

    }

    private static ChatRequestMessage getChatRequestMessage(
        String role,
        String content) {
        try {
            AuthorRole authorRole = AuthorRole.valueOf(role.toUpperCase(Locale.ROOT));
            return OpenAIChatCompletion.getChatRequestMessage(authorRole, content);
        } catch (IllegalArgumentException e) {
            LOGGER.debug("Unknown author role: " + role);
            throw new SKException("Unknown author role: " + role);
        }
    }

    public static ChatRequestMessage unescapeRequest(ChatRequestMessage message) {
        if (message instanceof ChatRequestUserMessage) {
            ChatRequestUserMessage chatRequestMessage = (ChatRequestUserMessage) message;
            String content = StringEscapeUtils.unescapeXml(
                chatRequestMessage.getContent().toString());

            return new ChatRequestUserMessage(content)
                .setName(chatRequestMessage.getName());
        } else if (message instanceof ChatRequestSystemMessage) {
            ChatRequestSystemMessage chatRequestMessage = (ChatRequestSystemMessage) message;
            String content = StringEscapeUtils.unescapeXml(chatRequestMessage.getContent());

            return new ChatRequestSystemMessage(content)
                .setName(chatRequestMessage.getName());
        } else if (message instanceof ChatRequestAssistantMessage) {
            ChatRequestAssistantMessage chatRequestMessage = (ChatRequestAssistantMessage) message;
            String content = StringEscapeUtils.unescapeXml(chatRequestMessage.getContent());

            return new ChatRequestAssistantMessage(content)
                .setToolCalls(chatRequestMessage.getToolCalls())
                .setFunctionCall(chatRequestMessage.getFunctionCall())
                .setName(chatRequestMessage.getName());
        } else if (message instanceof ChatRequestFunctionMessage) {
            ChatRequestFunctionMessage chatRequestMessage = (ChatRequestFunctionMessage) message;
            String content = StringEscapeUtils.unescapeXml(chatRequestMessage.getContent());

            return new ChatRequestFunctionMessage(
                chatRequestMessage.getName(),
                content);
        } else if (message instanceof ChatRequestToolMessage) {
            ChatRequestToolMessage chatRequestMessage = (ChatRequestToolMessage) message;
            String content = StringEscapeUtils.unescapeXml(chatRequestMessage.getContent());

            return new ChatRequestToolMessage(
                content,
                chatRequestMessage.getToolCallId());
        }

        throw new SKException("Unknown message type: " + message.getClass().getSimpleName());
    }
}