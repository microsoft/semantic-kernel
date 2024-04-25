package com.microsoft.semantickernel.aiservices.openai.assistants;

/**
 * Represents a text content annotation.
 */
public interface TextContentAnnotation {

    /**
     * The type of the content.
     * @return The type of the content.
     */
    TextContentAnnotationType getType();
}
