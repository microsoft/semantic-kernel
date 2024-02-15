package com.microsoft.semantickernel;

import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;

import java.util.Map;

import javax.annotation.Nullable;

/**
 * Base class which represents the content returned by a streaming AI service.
 * @param <T> The type of the content. 
 */
public abstract class StreamingKernelContent<T> extends KernelContent<T> {

    /**
     * In a scenario of multiple choices per request, this represents 
     * the zero-based index of the choice in the streaming sequence
     */
    private final int choiceIndex;

    /**
     * Initializes a new instance of the {@link StreamingKernelContent} class.
     * @param innerContent The inner content representation.
     * @param choiceIndex The zero-based index of the choice in the streaming sequence.
     * @param modelId The model identifier used to generate the content.
     * @param metadata The metadata associated with the content.
     */
    protected StreamingKernelContent(
        @Nullable T innerContent,
        int choiceIndex,
        @Nullable String modelId,
        @Nullable Map<String, ContextVariable<?>> metadata) {
        super(innerContent, modelId, null);
        this.choiceIndex = choiceIndex;
    }

    /**
     * Gets the zero-based index of the choice in the streaming sequence.
     * @return The zero-based index of the choice in the streaming sequence.
     */
    public int getChoiceIndex() {
        return choiceIndex;
    }
}
