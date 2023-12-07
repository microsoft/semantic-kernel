package com.microsoft.semantickernel.orchestration.contextvariables;

public class VariableType<T> {

    private final Converter<T> converter;
    private final Class<T> clazz;

    public VariableType(Converter<T> converter, Class<T> clazz) {
        this.converter = converter;
        this.clazz = clazz;
    }

    public Converter<T> getConverter() {
        return converter;
    }

    public Class<T> getClazz() {
        return clazz;
    }
}
