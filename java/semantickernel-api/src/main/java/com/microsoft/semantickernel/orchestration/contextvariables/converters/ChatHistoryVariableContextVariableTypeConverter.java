package com.microsoft.semantickernel.orchestration.contextvariables.converters;

import static com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes.convert;

import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter;

public class ChatHistoryVariableContextVariableTypeConverter extends
    ContextVariableTypeConverter<ChatHistory> {

    public ChatHistoryVariableContextVariableTypeConverter() {
        super(
            ChatHistory.class,
            s -> convert(s, ChatHistory.class),
            ChatHistoryVariableContextVariableTypeConverter::toXmlString,
            x -> {
                throw new UnsupportedOperationException(
                    "ChatHistoryVariableConverter does not support fromPromptString");
            }
        );
    }

    private static String toXmlString(ChatHistory chatHistory) {
        return chatHistory
            .getMessages()
            .stream()
            .map(message -> String.format("<message role=\"%s\">%s</message>%n",
                message.getAuthorRole(),
                message.getContent()))
            .reduce("", (acc, message) -> acc + message);
    }
}
