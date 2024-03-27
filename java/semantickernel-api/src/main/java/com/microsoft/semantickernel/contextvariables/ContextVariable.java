// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.contextvariables;

import com.azure.ai.openai.models.CompletionsUsage;
import com.microsoft.semantickernel.contextvariables.ContextVariableTypeConverter.NoopConverter;
import com.microsoft.semantickernel.exceptions.SKException;
import java.time.OffsetDateTime;
import java.util.Collections;
import java.util.Objects;
import javax.annotation.Nullable;

/**
 * A context variable wraps an arbitrary value and a {@code ContextVariableType}.
 * {@code ContextVariableType} is used throughout the Semantic Kernel for passing arguments to
 * functions and as function return types.
 *
 * @param <T> the type of the context variable
 */
public class ContextVariable<T> {

    private final ContextVariableType<T> type;

    @Nullable
    private final T value;

    /**
     * Creates a new instance of the {@link ContextVariable} class.
     *
     * @param type  the type
     * @param value the value
     */
    public ContextVariable(
        ContextVariableType<T> type,
        @Nullable T value) {
        this.type = type;
        this.value = value;
    }

    /**
     * Converts the given value to the requested result type.
     *
     * @param <T>                 the type of the requested result
     * @param <U>                 the type of the input value
     * @param it                  the input value
     * @param requestedResultType the requested result type
     * @return the converted value
     */
    public static <T, U> ContextVariable<T> convert(
        @Nullable U it,
        ContextVariableType<T> requestedResultType) {
        return convert(
            it,
            requestedResultType.getClazz(),
            new ContextVariableTypes(
                Collections.singletonList(requestedResultType.getConverter())));
    }

    /**
     * Converts the given value to the requested result type. The {@code ContextVariableTypes}
     * parameter is used to find the appropriate converter for the input value and the requested
     * result type.
     *
     * @param <T>                  the type of the requested result
     * @param <U>                  the type of the input value
     * @param it                   the input value
     * @param requestedResultType  the requested result type
     * @param contextVariableTypes the context variable types
     * @return the converted value
     * @throws SKException if a type converter cannot be found, or the input value cannot be
     *                     converted to the requested result type
     */
    public static <T, U> ContextVariable<T> convert(
        @Nullable U it,
        Class<T> requestedResultType,
        @Nullable ContextVariableTypes contextVariableTypes) {
        if (contextVariableTypes == null) {
            contextVariableTypes = new ContextVariableTypes();
        }

        if (it instanceof ContextVariable) {
            it = (U) ((ContextVariable<?>) it).getValue();
        }

        if (it == null) {
            return new ContextVariable<>(
                contextVariableTypes.getVariableTypeForClass(requestedResultType),
                null);
        }

        if (requestedResultType.isAssignableFrom(it.getClass())) {
            try {
                return contextVariableTypes
                    .getVariableTypeForClass(requestedResultType)
                    .of(requestedResultType.cast(it));
            } catch (Exception e) {
                return new ContextVariable<>(
                    new ContextVariableType<>(
                        new NoopConverter<>(requestedResultType),
                        requestedResultType),
                    requestedResultType.cast(it));
            }
        }

        ContextVariableType<T> requestedResultTypeVariable;

        try {
            requestedResultTypeVariable = contextVariableTypes.getVariableTypeForClass(
                requestedResultType);
        } catch (Exception e) {
            throw new SKException("Unable to find variable type for " + requestedResultType, e);
        }

        ContextVariableType<U> typeOfActualReturnedType = null;

        try {
            // First try to convert from type ? to T using the converter of ? and see if it can convert it to T.
            typeOfActualReturnedType = contextVariableTypes
                .getVariableTypeForClass((Class<U>) it.getClass());
        } catch (Exception e) {
            try {
                typeOfActualReturnedType = contextVariableTypes
                    .getVariableTypeForSuperClass((Class<U>) it.getClass());
            } catch (Exception e2) {
                // ignore
            }
        }

        if (typeOfActualReturnedType != null) {
            // Try the to object
            T converted = typeOfActualReturnedType.getConverter().toObject(contextVariableTypes, it,
                requestedResultType);

            if (converted != null) {
                return contextVariableTypes.getVariableTypeForClass(requestedResultType)
                    .of(converted);
            }

            if (requestedResultType.isAssignableFrom(String.class)) {
                // Try using toPromptString
                String str = typeOfActualReturnedType.getConverter()
                    .toPromptString(
                        contextVariableTypes,
                        typeOfActualReturnedType.getClazz().cast(it));

                return requestedResultTypeVariable.of(str);
            }
        }

        // Try getting a converter of type T and see if it can convert ? to T.
        if (requestedResultTypeVariable != null) {
            // Try using from object
            T result = requestedResultTypeVariable.getConverter().fromObject(it);
            if (result != null) {
                return requestedResultTypeVariable.of(result);
            }

            if (it.getClass().equals(String.class)) {
                // Try using from prompt string
                return requestedResultTypeVariable.of(
                    requestedResultTypeVariable.getConverter().fromPromptString((String) it));
            }
        }

        throw new SKException("Unable to convert " + it.getClass() + " to " + requestedResultType);
    }

    /**
     * Creates a new instance of the {@link ContextVariable} class without using strong typing.
     *
     * @param value the value
     * @param clazz the class
     * @param types the types
     * @return the new instance
     */
    @SuppressWarnings({ "rawtypes", "unchecked" })
    public static ContextVariable<?> untypedOf(
        @Nullable Object value,
        Class<?> clazz,
        ContextVariableTypes types) {
        ContextVariableType<?> type = types.getVariableTypeForClass(clazz);

        return new ContextVariable(type, value);
    }

    /**
     * Convenience method for creating a {@code ContextVariable} from the given
     * {@code CompletionsUsage} instance.
     *
     * @param x the value
     * @return the new instance
     */
    public static ContextVariable<CompletionsUsage> of(CompletionsUsage x) {
        return ofValue(x);
    }

    /**
     * Convenience method for creating a {@code ContextVariable} from the given
     * {@code OffsetDateTime} instance.
     *
     * @param x the value
     * @return the new instance
     */
    public static ContextVariable<OffsetDateTime> of(OffsetDateTime x) {
        return ofValue(x);
    }

    /**
     * Convenience method for creating a {@code ContextVariable} from the given {@code String}
     * instance.
     *
     * @param value the value
     * @return the new instance
     */
    public static ContextVariable<String> of(String value) {
        return ofValue(value);
    }

    /**
     * Convenience method for creating a {@code ContextVariable} from the given object.
     *
     * @param x the object
     * @return the new instance
     */
    public static ContextVariable<Object> ofGlobalType(Object x) {
        return ofValue(x);
    }

    @SuppressWarnings("unchecked")
    private static <T> ContextVariable<T> ofValue(T value) {
        Objects.requireNonNull(value, "value cannot be null");

        if (value instanceof ContextVariable) {
            return (ContextVariable<T>) value;
        }

        ContextVariableType<T> type = ContextVariableTypes.getGlobalVariableTypeForClass(
            (Class<T>) value.getClass());
        return new ContextVariable<>(type, value);
    }

    /**
     * Creates a new instance of the {@link ContextVariable} class.
     *
     * @param value     the value
     * @param converter the converter
     * @param <T>       the type of the value
     * @return the new instance
     */
    public static <T> ContextVariable<T> of(T value, ContextVariableTypeConverter<T> converter) {
        Objects.requireNonNull(value, "value cannot be null");
        Objects.requireNonNull(converter, "converter cannot be null");
        ContextVariableType<T> type = new ContextVariableType<>(converter, converter.getType());
        return new ContextVariable<>(type, value);
    }

    /**
     * Get the value of the context variable.
     *
     * @return the value
     */
    @Nullable
    public T getValue() {
        return value;
    }

    /**
     * Get the value of the context variable.
     *
     * @param clazz the class
     * @param <U>   the type of the value
     * @return the value
     * @throws SKException if the value cannot be cast to the requested type
     */
    @Nullable
    public <U> U getValue(Class<U> clazz) {
        try {
            return clazz.cast(value);
        } catch (ClassCastException e) {
            throw new SKException(
                "Cannot cast " + (value != null ? value.getClass() : "null") + " to " + clazz, e);
        }
    }

    /**
     * Get the type of the context variable.
     *
     * @return the type
     */
    public ContextVariableType<T> getType() {
        return type;
    }

    /**
     * Use the given {@code ContextVariableTypeConverter} to convert the value of this
     * {@code ContextVariable} to a prompt string. This method is useful when the convert of this
     * {@code ContextVariableType} does not create the expected prompt string.
     *
     * @param types     the types to use when converting the value
     * @param converter the converter to use when converting the value
     * @return the value of this {@code ContextVariable} as a prompt string
     */
    public String toPromptString(ContextVariableTypes types,
        ContextVariableTypeConverter<T> converter) {
        return converter.toPromptString(types, value);
    }

    /**
     * Use the given {@code ContextVariableTypeConverter} to convert the value of this
     * {@code ContextVariable} to a prompt string. This method is useful when the convert of this
     * {@code ContextVariableType} does not create the expected prompt string.
     *
     * @param types the types to use when converting the value
     * @return the value of this {@code ContextVariable} as a prompt string
     */
    public String toPromptString(ContextVariableTypes types) {
        return toPromptString(types, type.getConverter());
    }

    /**
     * Returns true if the value of this {@code ContextVariable} is {@code null} or empty.
     *
     * @return true if the value is {@code null} or empty
     */
    public boolean isEmpty() {
        return value == null || value.toString().isEmpty();
    }
}
