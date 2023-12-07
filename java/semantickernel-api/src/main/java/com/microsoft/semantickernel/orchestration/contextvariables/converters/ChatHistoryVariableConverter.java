package com.microsoft.semantickernel.orchestration.contextvariables.converters;

import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.orchestration.contextvariables.Converter;

import static com.microsoft.semantickernel.orchestration.contextvariables.VariableTypes.convert;

public class ChatHistoryVariableConverter extends Converter<ChatHistory> {

    public ChatHistoryVariableConverter() {
        super(
            ChatHistory.class,
            s -> convert(s, ChatHistory.class),
            Object::toString,
            x -> {
                throw new UnsupportedOperationException(
                    "ChatHistoryVariableConverter does not support fromPromptString");
            }
        );
    }
}
