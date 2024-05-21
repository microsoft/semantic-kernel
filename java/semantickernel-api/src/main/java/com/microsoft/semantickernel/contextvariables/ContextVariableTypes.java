// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.contextvariables;

import com.microsoft.semantickernel.contextvariables.converters.BooleanVariableContextVariableTypeConverter;
import com.microsoft.semantickernel.contextvariables.converters.CharacterVariableContextVariableTypeConverter;
import com.microsoft.semantickernel.contextvariables.converters.ChatHistoryVariableContextVariableTypeConverter;
import com.microsoft.semantickernel.contextvariables.converters.CollectionVariableContextVariableTypeConverter;
import com.microsoft.semantickernel.contextvariables.converters.CompletionUsageContextVariableTypeConverter;
import com.microsoft.semantickernel.contextvariables.converters.DateTimeContextVariableTypeConverter;
import com.microsoft.semantickernel.contextvariables.converters.InstantContextVariableTypeConverter;
import com.microsoft.semantickernel.contextvariables.converters.NumberVariableContextVariableTypeConverter;
import com.microsoft.semantickernel.contextvariables.converters.PrimitiveBooleanVariableContextVariableTypeConverter;
import com.microsoft.semantickernel.contextvariables.converters.StringVariableContextVariableTypeConverter;
import com.microsoft.semantickernel.contextvariables.converters.TextContentVariableContextVariableTypeConverter;
import com.microsoft.semantickernel.contextvariables.converters.VoidVariableContextVariableTypeConverter;
import com.microsoft.semantickernel.exceptions.SKException;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import javax.annotation.Nullable;

/**
 * A collection of context variable types, with converters to convert objects to the types.
 */
public class ContextVariableTypes {

    private static final ContextVariableTypes DEFAULT_TYPES;

    static {
        List<ContextVariableTypeConverter<?>> types = Arrays.asList(
            new CharacterVariableContextVariableTypeConverter(),
            new ChatHistoryVariableContextVariableTypeConverter(),
            new TextContentVariableContextVariableTypeConverter(),
            new StringVariableContextVariableTypeConverter(),
            new CollectionVariableContextVariableTypeConverter(),
            new VoidVariableContextVariableTypeConverter(),
            new ContextVariableTypeConverter<>(void.class, s -> null, s -> null, s -> null),
            new DateTimeContextVariableTypeConverter(),
            new InstantContextVariableTypeConverter(),
            new CompletionUsageContextVariableTypeConverter(),

            new BooleanVariableContextVariableTypeConverter(),
            new PrimitiveBooleanVariableContextVariableTypeConverter(),

            new NumberVariableContextVariableTypeConverter<>(Byte.class, Byte::parseByte,
                Number::byteValue),
            new NumberVariableContextVariableTypeConverter<>(byte.class, Byte::parseByte,
                Number::byteValue),

            new NumberVariableContextVariableTypeConverter<>(Integer.class, Integer::parseInt,
                Number::intValue),
            new NumberVariableContextVariableTypeConverter<>(int.class, Integer::parseInt,
                Number::intValue),

            new NumberVariableContextVariableTypeConverter<>(Long.class, Long::parseLong,
                Number::longValue),
            new NumberVariableContextVariableTypeConverter<>(long.class, Long::parseLong,
                Number::longValue),

            new NumberVariableContextVariableTypeConverter<>(Double.class, Double::parseDouble,
                Number::doubleValue),
            new NumberVariableContextVariableTypeConverter<>(double.class, Double::parseDouble,
                Number::doubleValue),

            new NumberVariableContextVariableTypeConverter<>(Float.class, Float::parseFloat,
                Number::floatValue),
            new NumberVariableContextVariableTypeConverter<>(float.class, Float::parseFloat,
                Number::floatValue),

            new NumberVariableContextVariableTypeConverter<>(Short.class, Short::parseShort,
                Number::shortValue),
            new NumberVariableContextVariableTypeConverter<>(short.class, Short::parseShort,
                Number::shortValue));
        DEFAULT_TYPES = new ContextVariableTypes(types);
    }

    private final Map<Class<?>, ContextVariableType<?>> variableTypes;

    /**
     * Create a new collection of context variable types.
     *
     * @param converters The converters to use to convert objects to the types.
     */
    public ContextVariableTypes(List<ContextVariableTypeConverter<?>> converters) {
        variableTypes = new HashMap<>();
        converters.forEach(this::putConverter);
    }

    /**
     * Create a new collection of context variable types.
     */
    public ContextVariableTypes() {
        variableTypes = new HashMap<>();
    }

    public static ContextVariableTypes getGlobalTypes() {
        return new ContextVariableTypes(DEFAULT_TYPES);
    }

    /**
     * Create a new collection of context variable types.
     *
     * @param contextVariableTypes The collection of context variable types to copy.
     */
    public ContextVariableTypes(ContextVariableTypes contextVariableTypes) {
        this.variableTypes = new HashMap<>(contextVariableTypes.variableTypes);
    }

    /**
     * Add a converter to the global collection of context variable type converters.
     *
     * @param converter The converter to add.
     * @see #getGlobalVariableTypeForClass(Class)
     */
    public static void addGlobalConverter(
        ContextVariableTypeConverter<?> converter) {
        DEFAULT_TYPES.putConverter(converter);
    }

    /**
     * Get the global context variable type for the given class.
     *
     * @param aClass The class to get the context variable type for.
     * @param <T>    The type of the context variable.
     * @return The context variable type for the given class.
     * @see #addGlobalConverter(ContextVariableTypeConverter)
     */
    public static <T> ContextVariableType<T> getGlobalVariableTypeForClass(Class<T> aClass) {
        return DEFAULT_TYPES.getVariableTypeForClass(aClass);
    }

    /**
     * Convert the given object to the given class, if possible.
     *
     * @param <T>   the type to convert to
     * @param s     the object to convert
     * @param clazz the class of the type to convert to
     * @return the converted object, or {@code null} if the object cannot be converted
     */
    @Nullable
    @SuppressWarnings("unchecked")
    public static <T> T convert(@Nullable Object s, Class<T> clazz) {
        if (s instanceof ContextVariable && ((ContextVariable<?>) s).getType().getClazz()
            .isAssignableFrom(clazz)) {
            return ((ContextVariable<T>) s).getValue();
        }
        if (s != null && clazz.isAssignableFrom(s.getClass())) {
            return clazz.cast(s);
        } else {
            return null;
        }
    }

    /**
     * Add a converter to this {@code ContextVariableTypes} instance.
     *
     * @param <T>                          The type of the context variable.
     * @param contextVariableTypeConverter the converter to add.
     */
    public <T> void putConverter(
        ContextVariableTypeConverter<T> contextVariableTypeConverter) {
        variableTypes.put(contextVariableTypeConverter.getType(),
            new ContextVariableType<>(contextVariableTypeConverter,
                contextVariableTypeConverter.getType()));
    }

    /**
     * Get the context variable type for the given class.
     *
     * @param aClass The class to get the context variable type for.
     * @param <T>    The type of the context variable.
     * @return The context variable type for the given class
     * @throws SKException if the type cannot be found.
     */
    @SuppressWarnings("unchecked")
    public <T> ContextVariableType<T> getVariableTypeForClass(Class<T> aClass) {
        try {
            return this.getVariableTypeForClassInternal(aClass);
        } catch (Exception e) {
            return DEFAULT_TYPES.getVariableTypeForClassInternal(aClass);
        }
    }

    /**
     * Get the context variable type for the given class or for a type that is assignable from the
     * given class. its super class.
     *
     * @param aClass The class to get the context variable type for.
     * @param <T>    The type of the context variable.
     * @return The context variable type for the given class.
     * @throws SKException if the type cannot be found.
     */
    @SuppressWarnings("unchecked")
    public <T> ContextVariableType<T> getVariableTypeForSuperClass(Class<T> aClass) {
        try {
            return this.getVariableTypeForSuperClassInternal(aClass);
        } catch (Exception e) {
            return DEFAULT_TYPES.getVariableTypeForSuperClassInternal(aClass);
        }
    }

    @SuppressWarnings("unchecked")
    private <T> ContextVariableType<T> getVariableTypeForClassInternal(Class<T> aClass) {
        ContextVariableType<?> contextVariableType = variableTypes.get(aClass);

        if (contextVariableType != null) {
            return (ContextVariableType<T>) contextVariableType;
        }

        return (ContextVariableType<T>) variableTypes
            .values()
            .stream()
            .filter(c -> {
                return c.getClazz().isAssignableFrom(aClass);
            })
            .findFirst()
            .orElseThrow(
                () -> new SKException("Unknown context variable type: " + aClass.getName()));
    }

    @SuppressWarnings("unchecked")
    private <T> ContextVariableType<T> getVariableTypeForSuperClassInternal(Class<T> aClass) {
        ContextVariableType<?> contextVariableType = variableTypes.get(aClass);

        if (contextVariableType != null) {
            return (ContextVariableType<T>) contextVariableType;
        }

        return (ContextVariableType<T>) variableTypes
            .values()
            .stream()
            .filter(c -> {
                return aClass.isAssignableFrom(c.getClazz());
            })
            .findFirst()
            .orElseThrow(
                () -> new SKException("Unknown context variable type: " + aClass.getName()));
    }

    /**
     * Add all the converters from the given collection to this collection.
     *
     * @param contextVariableTypes The collection of converters to add.
     */
    public void putConverters(ContextVariableTypes contextVariableTypes) {
        this.variableTypes.putAll(contextVariableTypes.variableTypes);
    }

    /**
     * Create a context variable of the given value.
     *
     * @param value The value to create a context variable of.
     * @param <T>   The type of the context variable.
     * @return The context variable of the given value.
     */
    public <T> ContextVariable<T> contextVariableOf(T value) {
        if (value instanceof ContextVariable) {
            return (ContextVariable<T>) value;
        }

        ContextVariableType<?> type = getVariableTypeForClass(value.getClass());

        if (type == null) {
            throw new SKException("Unknown type: " + value.getClass());
        }

        return (ContextVariable<T>) type.of(value);
    }
}