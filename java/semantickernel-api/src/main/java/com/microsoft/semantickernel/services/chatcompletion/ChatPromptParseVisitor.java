// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.services.chatcompletion;

import com.azure.core.util.BinaryData;
import javax.annotation.Nullable;

public interface ChatPromptParseVisitor<T> {

    ChatPromptParseVisitor<T> addMessage(String role, String content);

    ChatPromptParseVisitor<T> addFunction(String name, @Nullable String description,
        @Nullable BinaryData parameters);

    boolean areMessagesEmpty();

    ChatPromptParseVisitor<T> fromRawPrompt(String rawPrompt);

    T get();

    ChatPromptParseVisitor<T> reset();
}