package com.microsoft.semantickernel.orchestration.contextvariables;

public class ContextVariableType<T> {

    private final ContextVariableTypeConverter<T> contextVariableTypeConverter;
    private final Class<T> clazz;

    public ContextVariableType(ContextVariableTypeConverter<T> contextVariableTypeConverter, Class<T> clazz) {
        this.contextVariableTypeConverter = contextVariableTypeConverter;
        this.clazz = clazz;
    }

    public ContextVariableTypeConverter<T> getConverter() {
        return contextVariableTypeConverter;
    }

    public Class<T> getClazz() {
        return clazz;
    }
}
