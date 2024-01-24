package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;

public class FunctionResult<T> {

    private final ContextVariable<T> result;
    private final FunctionResultMetadata metadata;

    public FunctionResult(ContextVariable<T> result, FunctionResultMetadata metadata) {
        this.result = result;
        this.metadata = metadata;
    }

    public FunctionResult(ContextVariable<T> of) {
        this(of, FunctionResultMetadata.empty());
    }


    public T getResult() {
        return result.getValue();
    }

    public ContextVariable<T> getResultVariable() {
        return result;
    }

    public FunctionResultMetadata getMetadata() {
        return metadata;
    }
}
