package com.microsoft.semantickernel.orchestration.contextvariables.converters;

import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter;
import static com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes.convert;

/**
 * A {@link com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter} 
 * for {@code com.microsoft.semantickernel.chathistory.ChatHistory} variables. Use
 * {@code ContextVariableTypes.getGlobalVariableTypeForClass(ChatHistory.class)} 
 * to get an instance of this class.
 * @see com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes#getGlobalVariableTypeForClass(Class)
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
            });
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
