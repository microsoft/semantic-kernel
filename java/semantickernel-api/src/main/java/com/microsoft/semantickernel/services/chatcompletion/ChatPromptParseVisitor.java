package com.microsoft.semantickernel.services.chatcompletion;

import com.azure.core.util.BinaryData;

public interface ChatPromptParseVisitor<T> {

    ChatPromptParseVisitor<T> addMessage(String role, String content);

    ChatPromptParseVisitor<T> addFunction(String name, String description, BinaryData parameters);

    boolean areMessagesEmpty();

    ChatPromptParseVisitor<T> fromRawPrompt(String rawPrompt);

    T get();
}