package com.microsoft.semantickernel.orchestration.contextvariables;

import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter.NoopConverter;

public class NullContextVariable<T> extends ContextVariable<T> {

    public NullContextVariable(Class<T> type) {
        super(new ContextVariableType<>(
            new NoopConverter<>(type),
            type
        ), null);
    }
}
