package com.microsoft.semantickernel.orchestration.contextvariables;

import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

public class FunctionResult<T> {

    private final ContextVariable<T> result;
    private final Map<String, ContextVariable<?>> metadata;

    public FunctionResult(ContextVariable<T> result, Map<String, ContextVariable<?>> metadata) {
        this.result = result;
        this.metadata = new HashMap<>(metadata);
    }

    public FunctionResult(ContextVariable<T> of) {
        this(of, Collections.emptyMap());
    }


    public T getResult() {
        return result.getValue();
    }

    public ContextVariable<T> getResultVariable() {
        return result;
    }

    public Map<String, ContextVariable<?>> getMetadata() {
        return Collections.unmodifiableMap(metadata);
    }
}
