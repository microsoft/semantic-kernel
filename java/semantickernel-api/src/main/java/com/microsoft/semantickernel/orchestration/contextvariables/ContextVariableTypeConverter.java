package com.microsoft.semantickernel.orchestration.contextvariables;

import java.util.function.Function;

public class ContextVariableTypeConverter<T> {

    private final Class<T> clazz;
    private final Function<Object, T> fromObject;
    private final Function<T, String> toPromptString;
    private final Function<String, T> fromPromptString;

    public ContextVariableTypeConverter(
        Class<T> clazz,
        Function<Object, T> fromObject,
        Function<T, String> toPromptString,
        Function<String, T> fromPromptString) {
        this.clazz = clazz;
        this.fromObject = fromObject;
        this.toPromptString = toPromptString;
        this.fromPromptString = fromPromptString;

    }

    public T fromObject(Object s) {
        return fromObject.apply(s);
    }

    public String toPromptString(T t) {
        return toPromptString.apply(t);
    }

    public T fromPromptString(String t) {
        return fromPromptString.apply(t);
    }

    public Class<T> getType() {
        return clazz;
    }
}