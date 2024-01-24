package com.microsoft.semantickernel;

import com.microsoft.semantickernel.orchestration.FunctionResultMetadata;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import java.util.Map;
import javax.annotation.CheckForNull;
import javax.annotation.Nullable;

public abstract class KernelContent<T extends KernelContent<T>> {

    @Nullable
    private Object innerContent;
    @Nullable
    private String modelId;
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
    public FunctionResultMetadata getMetadata() {
        return metadata;
    }

    public abstract String getContent();
}
