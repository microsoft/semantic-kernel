package com.microsoft.semantickernel.aiservices.openai.assistants;

/**
 * The content of a message.
 */
public interface MessageContent {

    /**
     * The type of the content.
     * @return The type of the content.
     */
    MessageContentType getType();
}
