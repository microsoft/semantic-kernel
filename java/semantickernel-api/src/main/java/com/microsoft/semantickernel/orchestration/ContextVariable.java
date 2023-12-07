// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.orchestration.contextvariables.VariableType;
import com.microsoft.semantickernel.orchestration.contextvariables.VariableTypes;

public class ContextVariable<T> {

    private final VariableType<T> type;
    private final T value;

    public ContextVariable(VariableType<T> type, T value) {
        this.type = type;
        this.value = value;
    }

    public T getValue() {
        return value;
    }

    public VariableType<T> getType() {
        return type;
    }

    public String toPromptString() {
        return type.getConverter().toPromptString(value);
    }


    public boolean isEmpty() {
        return value == null || value.toString().isEmpty();
    }

    public ContextVariable<T> cloneVariable() {
        return new ContextVariable<T>(type, value);
    }

    public static <T> ContextVariable<T> of(T value) {
        VariableType<T> type = VariableTypes.getVariableTypeForClass(
            (Class<T>) value.getClass());
        return new ContextVariable<T>(type, value);
    }
}
