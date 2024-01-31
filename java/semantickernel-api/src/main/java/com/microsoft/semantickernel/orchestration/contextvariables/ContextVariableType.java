package com.microsoft.semantickernel.orchestration.contextvariables;

import javax.annotation.Nullable;

public class ContextVariableType<T> {

    private final ContextVariableTypeConverter<T> contextVariableTypeConverter;
    private final Class<T> clazz;

    public ContextVariableType(ContextVariableTypeConverter<T> contextVariableTypeConverter,
        Class<T> clazz) {
        this.contextVariableTypeConverter = contextVariableTypeConverter;
        this.clazz = clazz;
    }

    public ContextVariableTypeConverter<T> getConverter() {
        return contextVariableTypeConverter;
    }

    public Class<T> getClazz() {
        return clazz;
    }

    /**
     * Create a context variable of this type from the given object, converting it to type T if
     * necessary.
     *
     * @param it The object to convert.
     * @return A context variable of this type.
     */
    public ContextVariable<T> of(@Nullable Object it) {
        if (it == null) {
            return ContextVariable.of(clazz, clazz.cast(null));
        }

        if (clazz.isAssignableFrom(it.getClass())) {
            return ContextVariable.of(clazz.cast(it), getConverter());
        }
        ContextVariableTypeConverter<T> converter = getConverter();
        return ContextVariable.of(converter.getType(), converter.fromObject(it));
    }
}
