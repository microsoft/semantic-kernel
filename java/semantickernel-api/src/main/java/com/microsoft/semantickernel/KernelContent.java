package com.microsoft.semantickernel;

import com.microsoft.semantickernel.orchestration.FunctionResultMetadata;
import javax.annotation.Nullable;

public abstract class KernelContent<T extends KernelContent<T>> {

    @Nullable
    private Object innerContent;
    @Nullable
    private final String modelId;
    @Nullable
    private FunctionResultMetadata metadata;

    public KernelContent(
        @Nullable
        Object innerContent,
        @Nullable
        String modelId,
        @Nullable
        FunctionResultMetadata metadata
    ) {
        this.innerContent = innerContent;
        this.modelId = modelId;
        if (metadata != null) {
            this.metadata = metadata;
        }
    }

    KernelContent<T> setInnerContent(@Nullable Object innerContent) {
        this.innerContent = innerContent;
        return this;
    }

    @Nullable
    public Object getInnerContent() {
        return innerContent;
    }

    @Nullable
    public String getModelId() {
        return modelId;
    }

    @Nullable
    public FunctionResultMetadata getMetadata() {
        return metadata;
    }

    @Nullable
    public abstract String getContent();
}
