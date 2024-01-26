// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration.contextvariables;

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

    public <U> U getValue(Class<U> clazz) {
        if (clazz.isAssignableFrom(value.getClass())) {
            return (U) value;
        } else {
            throw new RuntimeException("Cannot cast " + value.getClass() + " to " + clazz);
        }
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
        return new ContextVariable<>(type, value);
    }

    @SuppressWarnings("unchecked")
    public static <T> ContextVariable<T> of(T value) {
        ContextVariableType<T> type = ContextVariableTypes.getDefaultVariableTypeForClass(
            (Class<T>) value.getClass());
        return new ContextVariable<>(type, value);
    }

    public static <T> ContextVariable<T> of(T value, ContextVariableTypeConverter<T> converter) {
        ContextVariableType<T> type = new ContextVariableType<>(converter, converter.getType());
        return new ContextVariable<>(type, value);
    }
}
