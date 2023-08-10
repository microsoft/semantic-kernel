// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.ai.openai.chatcompletion;

import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import javax.annotation.Nullable;

/** OpenAI Chat content */
public class OpenAIChatHistory extends ChatHistory {

    /**
     * Create a new and empty chat history
     *
     * @param assistantInstructions Optional instructions for the assistant
     */
    public OpenAIChatHistory(@Nullable String assistantInstructions) {
        super();

        if (assistantInstructions != null && !assistantInstructions.isEmpty()) {
            this.addSystemMessage(assistantInstructions);
        }
    }

    /**
     * Add a system message to the chat history
     *
     * @param content Message content
     */
    public void addSystemMessage(String content) {
        this.addMessage(AuthorRoles.System, content);
    }

    /**
     * Add an assistant message to the chat history
     *
     * @param content Message content
     */
    public void addAssistantMessage(String content) {
        this.addMessage(AuthorRoles.Assistant, content);
    }

    /**
     * Add a user message to the chat history
     *
     * @param content Message content
     */
    public void addUserMessage(String content) {
        this.addMessage(AuthorRoles.User, content);
    }
}
