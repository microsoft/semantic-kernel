package com.microsoft.semantickernel;

import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import java.util.Map;
import javax.annotation.Nullable;

public abstract class StreamingKernelContent<T> {

    /// <summary>
    /// The inner content representation. Use this to bypass the current abstraction.
    /// </summary>
    /// <remarks>
    /// The usage of this property is considered "unsafe". Use it only if strictly necessary.
    /// </remarks>
    @Nullable
    private final T innerContent;

    /// <summary>
    /// In a scenario of multiple choices per request, this represents zero-based index of the choice in the streaming sequence
    /// </summary>
    private final int choiceIndex;

    /// <summary>
    /// The model ID used to generate the content.
    /// </summary>
    @Nullable
    private String modelId;

    /// <summary>
    /// The metadata associated with the content.
    /// </summary>
    @Nullable
    private final Map<String, ContextVariable<?>> metadata;

    protected StreamingKernelContent(
        @Nullable T innerContent,
        int choiceIndex,
        @Nullable String modelId,
        @Nullable Map<String, ContextVariable<?>> metadata) {
        this.innerContent = innerContent;
        this.choiceIndex = choiceIndex;
        this.modelId = modelId;
        this.metadata = metadata;
    }
}
