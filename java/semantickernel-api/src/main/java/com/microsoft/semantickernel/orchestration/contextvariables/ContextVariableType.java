package com.microsoft.semantickernel.orchestration.contextvariables;

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
    public ContextVariable<T> of(Object it) {
        if (getClazz().isAssignableFrom(it.getClass())) {
            return ContextVariable.of((T) it, getConverter());
        }
        return ContextVariable.of(getConverter().fromObject(it));
    }
}
