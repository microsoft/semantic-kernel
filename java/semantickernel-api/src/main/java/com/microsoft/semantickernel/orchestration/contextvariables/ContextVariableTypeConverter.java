package com.microsoft.semantickernel.orchestration.contextvariables;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Optional;
import java.util.function.Function;
import javax.annotation.Nullable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * A converter for a context variable type. This class is used to convert objects to and from a
 * prompt string, and to convert objects to the type of the context variable.
 * @param <T> the type of the context variable
 */
public class ContextVariableTypeConverter<T> {

    private static final Logger LOGGER = LoggerFactory.getLogger(
        ContextVariableTypeConverter.class);

    private final Class<T> clazz;
    private final Function<Object, T> fromObject;
    private final Function<T, String> toPromptString;
    private final Function<String, T> fromPromptString;
    private final List<Converter<T, ?>> toObjects;

    /**
     * A converter from one type to another.
     * @param <T> the source type
     * @param <U> the target type
     */
    public interface Converter<T, U> {

        /**
         * Convert the object to the target type.
         * @param t the object to convert
         * @return the converted object
         */
        U toObject(T t);

        /**
         * Get the class of the target type.
         * @return the class of the target type
         */
        Class<U> getTargetType();
    }

    /**
     * A converter that does no conversion. This converter is often used as a default when no
     * other conveter can be found for the type. 
     * @param <T> the type of the context variable
     */
    public static class NoopConverter<T> extends ContextVariableTypeConverter<T> {

        /**
         * Create a new noop converter.
         * @param clazz the class of the type
         */
        public NoopConverter(Class<T> clazz) {
            super(
                clazz,
                x -> {
                    return (T) x;
                },
                x -> {
                    throw new RuntimeException("Noop converter should not be called");
                },
                x -> {
                    throw new RuntimeException("Noop converter should not be called");
                });
        }
    }

    /**
     * A base class for concrete implementations of {@link ContextVariableTypeConverter.Converter}.
     * @param <T> the source type
     * @param <U> the target type
     */
    public static abstract class DefaultConverter<T, U> implements Converter<T, U> {

        private final Class<U> targetType;

        protected DefaultConverter(Class<T> sourceType, Class<U> targetType) {
            this.targetType = targetType;
        }

        @Override
        public Class<U> getTargetType() {
            return targetType;
        }
    }

    /**
     * Create a new context variable type converter.
     * @param clazz the class of the type
     * @param fromObject a function to convert an object to the type
     * @param toPromptString a function to convert the type to a prompt string
     * @param fromPromptString a function to convert a prompt string to the type
     */
    public ContextVariableTypeConverter(
        Class<T> clazz,
        Function<Object, T> fromObject,
        Function<T, String> toPromptString,
        Function<String, T> fromPromptString) {
        this(clazz, fromObject, toPromptString, fromPromptString, Collections.emptyList());
    }

    /**
     * Create a new context variable type converter.
     * @param clazz the class of the type
     * @param fromObject a function to convert an object to the type
     * @param toPromptString a function to convert the type to a prompt string
     * @param fromPromptString a function to convert a prompt string to the type
     * @param toObjects a list of converters to convert the type to other types
     */
    public ContextVariableTypeConverter(
        Class<T> clazz,
        Function<Object, T> fromObject,
        Function<T, String> toPromptString,
        Function<String, T> fromPromptString,
        List<Converter<T, ?>> toObjects) {
        this.clazz = clazz;
        this.fromObject = fromObject;
        this.toPromptString = toPromptString;
        this.fromPromptString = fromPromptString;
        this.toObjects = new ArrayList<>(toObjects);
    }

    /**
     * Use this converter to convert the object to the type of the context variable.
     * @param <U> the type to convert to
     * @param t the object to convert
     * @param clazz the class of the type to convert to
     * @return the converted object
     */
    @Nullable
    @SuppressWarnings("unchecked")
    public <U> U toObject(@Nullable Object t, Class<U> clazz) {
        if (t == null) {
            return null;
        }

        Optional<Converter<T, ?>> converter = toObjects
            .stream()
            .filter(c -> c.getTargetType().equals(clazz))
            .findFirst();

        if (converter.isPresent()) {
            return (U) converter.get().toObject((T) t);
        }

        converter = toObjects
            .stream()
            .filter(c -> clazz.isAssignableFrom(c.getTargetType()))
            .findFirst();

        if (converter.isPresent()) {
            return (U) converter.get().toObject((T) t);
        }

        LOGGER.warn("No converter found for {} to {}", t.getClass(), clazz);
        return null;
    }

    /**
     * Convert the object to the type of the context variable using the {@code fromObject} function
     * provided to the constructor.
     * @param s the object to convert
     * @return the converted object
     */
    @Nullable
    public T fromObject(@Nullable Object s) {
        if (s == null) {
            return null;
        }
        return fromObject.apply(s);
    }

    /**
     * Convert the type to a prompt string using the {@code toPromptString} function provided to the
     * constructor.
     * @param t the type to convert
     * @return the prompt string
     */
    public String toPromptString(@Nullable T t) {
        if (t == null) {
            return "";
        }
        return toPromptString.apply(t);
    }

    /**
     * Convert the prompt string to the type using the {@code fromPromptString} function provided to
     * the constructor.
     * @param t the prompt string to convert
     * @return the type
     */
    @Nullable
    public T fromPromptString(@Nullable String t) {
        if (t == null) {
            return null;
        }
        return fromPromptString.apply(t);
    }

    /**
     * Get the class of the type.
     * @return the class of the type
     */
    public Class<T> getType() {
        return clazz;
    }
}