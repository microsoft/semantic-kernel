// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration.contextvariables;

import java.util.Objects;

import com.microsoft.semantickernel.exceptions.SKException;

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
        try {
            return clazz.cast(value);
        } catch (ClassCastException e) {
            throw new SKException("Cannot convert value to " + clazz, e);
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
        Objects.requireNonNull(value, "value cannot be null");

        if (value instanceof ContextVariable) {
            return (ContextVariable<T>) value;
        }

        ContextVariableType<T> type = ContextVariableTypes.getDefaultVariableTypeForClass(
            (Class<T>) value.getClass());
        return new ContextVariable<>(type, value);
    }

    public static <T> ContextVariable<T> of(T value, ContextVariableTypeConverter<T> converter) {
        Objects.requireNonNull(value, "value cannot be null");
        Objects.requireNonNull(converter, "converter cannot be null");
        ContextVariableType<T> type = new ContextVariableType<>(converter, converter.getType());
        return new ContextVariable<>(type, value);
    }
}
