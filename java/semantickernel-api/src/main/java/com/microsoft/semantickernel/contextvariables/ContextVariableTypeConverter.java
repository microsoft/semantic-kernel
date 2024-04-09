// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.contextvariables;

import com.microsoft.semantickernel.exceptions.SKException;
import edu.umd.cs.findbugs.annotations.SuppressFBWarnings;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Optional;
import java.util.function.Function;
import javax.annotation.Nullable;
import org.apache.commons.text.StringEscapeUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * A converter for a context variable type. This class is used to convert objects to and from a
 * prompt string, and to convert objects to the type of the context variable.
 *
 * @param <T> the type of the context variable
 */
public class ContextVariableTypeConverter<T> {

    private static final Logger LOGGER = LoggerFactory.getLogger(
        ContextVariableTypeConverter.class);

    public interface ToPromptStringFunction<T> {

        String toPromptString(ContextVariableTypes types, T t);
    }

    private final Class<T> clazz;
    private final Function<Object, T> fromObject;
    private final ToPromptStringFunction<T> toPromptString;
    private final Function<String, T> fromPromptString;
    private final List<Converter<T, ?>> toObjects;

    /**
     * Create a new context variable type converter.
     *
     * @param clazz            the class of the type
     * @param fromObject       a function to convert an object to the type
     * @param toPromptString   a function to convert the type to a prompt string
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
     *
     * @param clazz            the class of the type
     * @param fromObject       a function to convert an object to the type
     * @param toPromptString   a function to convert the type to a prompt string
     * @param fromPromptString a function to convert a prompt string to the type
     */
    public ContextVariableTypeConverter(
        Class<T> clazz,
        Function<Object, T> fromObject,
        ToPromptStringFunction<T> toPromptString,
        Function<String, T> fromPromptString) {
        this(clazz, fromObject, toPromptString, fromPromptString, Collections.emptyList());
    }

    /**
     * Create a new context variable type converter.
     *
     * @param clazz            the class of the type
     * @param fromObject       a function to convert an object to the type
     * @param toPromptString   a function to convert the type to a prompt string
     * @param fromPromptString a function to convert a prompt string to the type
     * @param toObjects        a list of converters to convert the type to other types
     */
    public ContextVariableTypeConverter(
        Class<T> clazz,
        Function<Object, T> fromObject,
        ToPromptStringFunction<T> toPromptString,
        Function<String, T> fromPromptString,
        List<Converter<T, ?>> toObjects) {
        this.clazz = clazz;
        this.fromObject = fromObject;
        this.toPromptString = toPromptString;
        this.fromPromptString = fromPromptString;
        this.toObjects = new ArrayList<>(toObjects);
    }

    /**
     * Create a new context variable type converter.
     *
     * @param clazz            the class of the type
     * @param fromObject       a function to convert an object to the type
     * @param toPromptString   a function to convert the type to a prompt string
     * @param fromPromptString a function to convert a prompt string to the type
     * @param toObjects        a list of converters to convert the type to other types
     */
    public ContextVariableTypeConverter(
        Class<T> clazz,
        Function<Object, T> fromObject,
        Function<T, String> toPromptString,
        Function<String, T> fromPromptString,
        List<Converter<T, ?>> toObjects) {
        this.clazz = clazz;
        this.fromObject = fromObject;
        this.toPromptString = (types, t) -> toPromptString.apply(t);
        this.fromPromptString = fromPromptString;
        this.toObjects = new ArrayList<>(toObjects);
    }

    /**
     * Use this converter to convert the object to the type of the context variable.
     *
     * @param <U>   the type to convert to
     * @param t     the object to convert
     * @param clazz the class of the type to convert to
     * @return the converted object
     */
    @Nullable
    @SuppressWarnings("unchecked")
    public <U> U toObject(ContextVariableTypes types, @Nullable Object t, Class<U> clazz) {
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
     *
     * @param s the object to convert
     * @return the converted object
     */
    @Nullable
    public T fromObject(@Nullable Object s) {
        if (s == null) {
            return null;
        }
        if (s instanceof ContextVariable) {
            return fromObject.apply(((ContextVariable<?>) s).getValue());
        }
        return fromObject.apply(s);
    }

    /**
     * Convert the type to a prompt string using the {@code toPromptString} function provided to the
     * constructor.
     *
     * @param t the type to convert
     * @return the prompt string
     */
    public String toPromptString(ContextVariableTypes types, @Nullable T t) {
        if (t == null) {
            return "";
        }
        return toPromptString.toPromptString(types, t);
    }

    /**
     * Convert the prompt string to the type using the {@code fromPromptString} function provided to
     * the constructor.
     *
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
     *
     * @return the class of the type
     */
    public Class<T> getType() {
        return clazz;
    }

    /**
     * A converter from one type to another.
     *
     * @param <T> the source type
     * @param <U> the target type
     */
    public interface Converter<T, U> {

        /**
         * Convert the object to the target type.
         *
         * @param t the object to convert
         * @return the converted object
         */
        U toObject(T t);

        /**
         * Get the class of the target type.
         *
         * @return the class of the target type
         */
        Class<U> getTargetType();
    }

    /**
     * A converter that does no conversion. This converter is often used as a default when no other
     * conveter can be found for the type.
     *
     * @param <T> the type of the context variable
     */
    public static class NoopConverter<T> extends ContextVariableTypeConverter<T> {

        /**
         * Create a new noop converter.
         *
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
     *
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
     * Create a new builder for a context variable type converter.
     *
     * @param <T>   the type of the context variable
     * @param clazz the class of the type
     * @return the builder
     */
    public static <T> Builder<T> builder(Class<T> clazz) {
        return new Builder<>(clazz);
    }

    /**
     * A builder for a context variable type converter.
     */
    public static class Builder<T> {

        private final Class<T> clazz;
        private Function<Object, T> fromObject;
        private ToPromptStringFunction<T> toPromptString;
        private Function<String, T> fromPromptString;

        /**
         * Create a new builder for a context variable type converter.
         *
         * @param clazz the class of the type
         */
        @SuppressFBWarnings("CT_CONSTRUCTOR_THROW")
        public Builder(Class<T> clazz) {
            this.clazz = clazz;
            fromObject = x -> {
                throw new UnsupportedOperationException("fromObject not implemented");
            };
            toPromptString = (a, b) -> {
                throw new UnsupportedOperationException("toPromptString not implemented");
            };
            fromPromptString = x -> {
                throw new UnsupportedOperationException("fromPromptString not implemented");
            };
        }

        /**
         * Make this builder a proxy for another type converter.
         *
         * @return this builder
         */
        public Builder<T> proxyGlobalType() {
            ContextVariableType<T> existingType = ContextVariableTypes
                .getGlobalVariableTypeForClass(
                    clazz);
            if (existingType == null) {
                throw new SKException(
                    "Asked to proxy a global type that does not exist: " + clazz.getName());
            }
            return proxyType(existingType.getConverter());
        }

        /**
         * Make this builder a proxy for another type converter.
         *
         * @param proxy the proxy type converter
         * @return this builder
         */
        public Builder<T> proxyType(ContextVariableTypeConverter<T> proxy) {
            this.fromObject = proxy.fromObject;
            this.toPromptString = proxy.toPromptString;
            this.fromPromptString = proxy.fromPromptString;
            return this;
        }

        /**
         * Set the function to convert an object to the type.
         *
         * @param fromObject the function to convert an object to the type
         * @return this builder
         */
        public Builder<T> fromObject(Function<Object, T> fromObject) {
            this.fromObject = fromObject;
            return this;
        }

        /**
         * Set the function to convert the type to a prompt string.
         *
         * @param toPromptString the function to convert the type to a prompt string
         * @return this builder
         */
        public Builder<T> toPromptString(Function<T, String> toPromptString) {
            this.toPromptString = (ignore, a) -> toPromptString.apply(a);
            return this;
        }

        /**
         * Set the function to convert a prompt string to the type.
         *
         * @param fromPromptString the function to convert a prompt string to the type
         * @return this builder
         */
        public Builder<T> fromPromptString(Function<String, T> fromPromptString) {
            this.fromPromptString = fromPromptString;
            return this;
        }

        /**
         * Build the context variable type converter.
         *
         * @return the context variable type converter
         */
        public ContextVariableTypeConverter<T> build() {
            return new ContextVariableTypeConverter<>(
                clazz,
                fromObject,
                toPromptString,
                fromPromptString);
        }
    }

    /**
     * To be used when toPromptString is called
     *
     * @param value the value to escape
     * @return the escaped value
     */
    @Nullable
    public static String escapeXmlString(@Nullable String value) {
        if (value == null) {
            return null;
        }
        return StringEscapeUtils.escapeXml11(value);
    }
}