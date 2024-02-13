package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import javax.annotation.Nullable;

public class FunctionResult<T> {

    private final ContextVariable<T> result;
    private final FunctionResultMetadata metadata;

    public FunctionResult(
        ContextVariable<T> result,
        @Nullable FunctionResultMetadata metadata) {
        this.result = result;
        this.metadata = metadata == null ? FunctionResultMetadata.empty() : metadata;
    }

    public FunctionResult(ContextVariable<T> of) {
        this(of, FunctionResultMetadata.empty());
    }

    /**
     * Get the result of the function invocation.
     * <p>
     * NOTE: IF YOU GET ClassCastException FROM THIS TRY ADDING withResultType() TO THE FUNCTION
     * INVOCATION
     *
     * @return The result of the function invocation.
     */
    @Nullable
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
