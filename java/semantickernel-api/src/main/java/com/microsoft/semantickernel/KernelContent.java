package com.microsoft.semantickernel;

import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import java.util.Map;

import javax.annotation.CheckForNull;
import javax.annotation.Nullable;

public class KernelContent<T extends KernelContent<T>> {

    @Nullable
    private Object innerContent;
    @Nullable
    private String modelId;
    @Nullable
    private Map<String, ContextVariable<?>> metadata;

    public KernelContent(
        @Nullable
        Object innerContent,
        @Nullable
        String modelId,
        @Nullable
        Map<String, ContextVariable<?>> metadata
    ) {
        this.innerContent = innerContent;
        this.modelId = modelId;
        this.metadata = metadata;
    }

    T setInnerContent(@Nullable Object innerContent) {
        this.innerContent = innerContent;
        return (T) this;
    }

    @CheckForNull
    public Object getInnerContent() {
        return innerContent;
    }

    @CheckForNull
    public String getModelId() {
        return modelId;
    }

    @CheckForNull
    public Map<String, ContextVariable<?>> getMetadata() {
        return metadata;
    }

}
