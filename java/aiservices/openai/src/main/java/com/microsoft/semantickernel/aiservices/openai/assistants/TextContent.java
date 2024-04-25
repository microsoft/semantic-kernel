
package com.microsoft.semantickernel.aiservices.openai.assistants;

import java.util.List;

/**
 * Represents text content within a message.
 */
public interface TextContent extends MessageContent {

    @Override
    default MessageContentType getType() { return MessageContentType.TEXT; }

    /**
     * The data that makes up the text.
     * @return The data that makes up the text.
     */
    public String getValue();

    /**
     * Metadata about the text.
     * @return Metadata about the text.
     */
    public List<TextContentAnnotation> getAnnotations();
}
