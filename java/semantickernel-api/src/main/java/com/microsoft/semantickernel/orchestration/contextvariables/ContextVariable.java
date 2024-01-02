// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration.contextvariables;

import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableType;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes;

public class ContextVariable<T> {

    private final ContextVariableType<T> type;
    private final T value;

    public ContextVariable(ContextVariableType<T> type, T value) {
        this.type = type;
        this.value = value;
    }

    public T getValue() {
        return value;
    }

    public ContextVariableType<T> getType() {
        return type;
    }

    public String toPromptString(ContextVariableTypeConverter<T> converter) {
        return converter.toPromptString(value);
    }

    public String toPromptString() {
        return toPromptString(type.getConverter());
    }

    public boolean isEmpty() {
        return value == null || value.toString().isEmpty();
    }

    public ContextVariable<T> cloneVariable() {
        return new ContextVariable<T>(type, value);
    }

    public static <T> ContextVariable<T> of(T value) {
        ContextVariableType<T> type = ContextVariableTypes.getDefaultVariableTypeForClass(
            (Class<T>) value.getClass());
        return new ContextVariable<T>(type, value);
    }
}
