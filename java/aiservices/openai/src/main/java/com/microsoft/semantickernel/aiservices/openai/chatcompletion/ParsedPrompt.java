package com.microsoft.semantickernel.aiservices.openai.chatcompletion;

import com.azure.ai.openai.models.ChatRequestMessage;
import com.azure.ai.openai.models.FunctionDefinition;
import java.util.List;

class ParsedPrompt {

    private final List<ChatRequestMessage> chatRequestMessages;
    private final List<FunctionDefinition> functions;

    protected ParsedPrompt(List<ChatRequestMessage> parsedMessages,
        List<FunctionDefinition> parsedFunctions) {
        this.chatRequestMessages = parsedMessages;
        this.functions = parsedFunctions;
    }

    public List<ChatRequestMessage> getChatRequestMessages() {
        return chatRequestMessages;
    }

    public List<FunctionDefinition> getFunctions() {
        return functions;
    }
}