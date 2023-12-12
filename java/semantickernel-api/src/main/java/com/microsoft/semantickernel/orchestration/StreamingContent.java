package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;

public class StreamingContent<T> {

    /// <summary>
    /// In a scenario of multiple choices per request, this represents zero-based index of the choice in the streaming sequence
    /// </summary>
    public int choiceIndex;

    /// <summary>
    /// The inner content representation. Use this to bypass the current abstraction.
    /// </summary>
    /// <remarks>
    /// The usage of this property is considered "unsafe". Use it only if strictly necessary.
    /// </remarks>
    public T innerContent;

    /// <summary>
    /// The model ID used to generate the content.
    /// </summary>
    public String modelId;

    /// <summary>
    /// The metadata associated with the content.
    /// </summary>
    public KernelArguments metadata;


    public StreamingContent(T content) {
        this.innerContent = content;
    }
}
