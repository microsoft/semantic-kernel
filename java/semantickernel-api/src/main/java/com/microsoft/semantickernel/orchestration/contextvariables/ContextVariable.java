// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration.contextvariables;

import java.util.Objects;

import javax.annotation.Nullable;

import com.microsoft.semantickernel.exceptions.SKException;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter.NoopConverter;
import java.util.Arrays;
import java.util.Objects;
import javax.annotation.Nullable;

public class ContextVariable<T> {

    private final ContextVariableType<T> type;

    @Nullable
    private final T value;

    public ContextVariable(ContextVariableType<T> type,
        @Nullable T value) {
        this.type = type;
        this.value = value;
    }

    public static <T> ContextVariable<T> of(Class<T> type, @Nullable T t) {
        if (t == null) {
            return new ContextVariable<>(
                ContextVariableTypes.getDefaultVariableTypeForClass(type),
                null);
        }

        return of(t);
    }

    @SuppressWarnings("rawtypes")
    public static ContextVariable<?> untypedOf(
        @Nullable Object value,
        Class<?> clazz) {
        ContextVariableType<?> type = ContextVariableTypes.getDefaultVariableTypeForClass(clazz);
        return new ContextVariable(type, value);
    }

    public static ContextVariable<?> untypedOf(
        @Nullable Object value,
        ContextVariableTypeConverter<?> converter) {
        ContextVariableType<?> type = new ContextVariableType(converter, converter.getType());
        return new ContextVariable(type, value);
    }

    public static <T, U> ContextVariable<T> convert(
        @Nullable
        U it,
        ContextVariableType<T> requestedResultType) {
        try {
            return convert(
                it,
                requestedResultType.getClazz(),
                new ContextVariableTypes(
                    Arrays.asList(requestedResultType.getConverter()))
            );

        } catch (Exception e) {
            return convert(
                it,
                requestedResultType.getClazz(),
                ContextVariableTypes.DEFAULT_TYPES
            );
        }

    }

    public static <T, U> ContextVariable<T> convert(
        @Nullable
        U it,
        Class<T> requestedResultType) {
        return convert(
            it,
            requestedResultType,
            ContextVariableTypes.DEFAULT_TYPES
        );
    }

    public static <T, U> ContextVariable<T> convert(
        @Nullable
        U it,
        Class<T> requestedResultType,
        ContextVariableTypes contextVariableTypes) {
        if (it == null) {
            return new ContextVariable<>(
                contextVariableTypes.getVariableTypeForClass(requestedResultType),
                null);
        }

        if (requestedResultType.isAssignableFrom(it.getClass())) {
            try {
                return ContextVariable.of(requestedResultType, requestedResultType.cast(it));
            } catch (Exception e) {
                return new ContextVariable<>(
                    new ContextVariableType<>(
                        new NoopConverter<>(requestedResultType),
                        requestedResultType
                    ),
                    requestedResultType.cast(it)
                );
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
            T converted = typeOfActualReturnedType.getConverter().toObject(it, requestedResultType);

            if (converted != null) {
                return contextVariableTypes.getVariableTypeForClass(requestedResultType)
                    .of(converted);
            }

            if (requestedResultType.isAssignableFrom(String.class)) {
                // Try using toPromptString
                String str = typeOfActualReturnedType.getConverter()
                    .toPromptString(typeOfActualReturnedType.getClazz().cast(it));

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

            if (requestedResultType.equals(String.class)) {
                // Try using from prompt string
                return requestedResultTypeVariable.of(
                    requestedResultTypeVariable.getConverter().fromPromptString((String) it));
            }
        }

        throw new SKException("Unable to convert " + it.getClass() + " to " + requestedResultType);
    }

    @Nullable
    public T getValue() {
        return value;
    }

    @Nullable
    public <U> U getValue(Class<U> clazz) {
        try {
            return clazz.cast(value);
        } catch (ClassCastException e) {
            throw new SKException(
                "Cannot cast " + (value != null ? value.getClass() : "null") + " to " + clazz, e);
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
