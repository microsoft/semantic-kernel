package com.microsoft.semantickernel.orchestration.contextvariables;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Optional;
import java.util.function.Function;
import javax.annotation.Nullable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ContextVariableTypeConverter<T> {

    private static final Logger LOGGER = LoggerFactory.getLogger(
        ContextVariableTypeConverter.class);

    private final Class<T> clazz;
    private final Function<Object, T> fromObject;
    private final Function<T, String> toPromptString;
    private final Function<String, T> fromPromptString;
    private final List<Converter<T, ?>> toObjects;

    public interface Converter<T, U> {

        U toObject(T t);

        Class<U> getTargetType();
    }

    public static class NoopConverter<T> extends ContextVariableTypeConverter<T> {

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

    public ContextVariableTypeConverter(
        Class<T> clazz,
        Function<Object, T> fromObject,
        Function<T, String> toPromptString,
        Function<String, T> fromPromptString) {
        this(clazz, fromObject, toPromptString, fromPromptString, Collections.emptyList());
    }

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

    
    @Nullable
    @SuppressWarnings("unchecked")
    public <U> U toObject(Object t, Class<U> clazz) {
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

    @Nullable
    public T fromObject(Object s) {
        if (s == null) {
            return null;
        }
        return fromObject.apply(s);
    }

    public String toPromptString(T t) {
        if (t == null) {
            return "";
        }
        return toPromptString.apply(t);
    }

    @Nullable
    public T fromPromptString(String t) {
        if (t == null) {
            return null;
        }
        return fromPromptString.apply(t);
    }

    public Class<T> getType() {
        return clazz;
    }
}