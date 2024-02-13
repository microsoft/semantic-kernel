package com.microsoft.semantickernel.orchestration.contextvariables.converters;

import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter;
import static com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes.convert;

/**
 * A {@link ContextVariableTypeConverter} for {@link ChatHistory} variables.
 * Typically, one will use the {@link ContextVariableTypes.get }
 */
public class ChatHistoryVariableContextVariableTypeConverter extends
    ContextVariableTypeConverter<ChatHistory> {

    /**
     * Initializes a new instance of the {@link ChatHistoryVariableContextVariableTypeConverter} class.
     */
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

    /*
     * Converts a {@link ChatHistory} to an XML string.
     */
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
