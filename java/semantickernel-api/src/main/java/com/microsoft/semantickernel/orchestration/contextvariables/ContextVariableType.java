package com.microsoft.semantickernel.orchestration.contextvariables;

import javax.annotation.Nullable;

/**
 * A type of context variable, with a converter to convert objects to the type.
 *
 * @param <T> The type of the context variable.
 */
public class ContextVariableType<T> {

    private final ContextVariableTypeConverter<T> contextVariableTypeConverter;
    private final Class<T> clazz;

    /**
     * Create a new context variable type.
     *
     * @param contextVariableTypeConverter The converter to convert objects to the type.
     * @param clazz The class of the type
     */
    public ContextVariableType(ContextVariableTypeConverter<T> contextVariableTypeConverter,
        Class<T> clazz) {
        this.contextVariableTypeConverter = contextVariableTypeConverter;
        this.clazz = clazz;
    }

    /**
     * Get the converter for this type.
     *
     * @return The converter for this type.
     */
    public ContextVariableTypeConverter<T> getConverter() {
        return contextVariableTypeConverter;
    }

    /**
     * Get the class of the type.
     *
     * @return The class of the type.
     */
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
            return new ContextVariable<>(
                this,
                clazz.cast(null)
            );
        }

        if (clazz.isAssignableFrom(it.getClass())) {
            return ContextVariable.of(clazz.cast(it), getConverter());
        }
        ContextVariableTypeConverter<T> converter = getConverter();

        return new ContextVariable<>(
            this,
            converter.fromObject(it)
        );
    }

}
