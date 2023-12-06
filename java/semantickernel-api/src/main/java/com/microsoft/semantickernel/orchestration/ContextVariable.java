// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.orchestration.contextvariables.PrimativeContextVariable.BooleanVariable;
import com.microsoft.semantickernel.orchestration.contextvariables.PrimativeContextVariable.CharacterVariable;
import com.microsoft.semantickernel.orchestration.contextvariables.PrimativeContextVariable.ChatHistoryVariable;
import com.microsoft.semantickernel.orchestration.contextvariables.PrimativeContextVariable.NumberVariable;
import com.microsoft.semantickernel.orchestration.contextvariables.PrimativeContextVariable.StringVariable;
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;
import java.util.function.Function;

public abstract class ContextVariable<T> {

    private T value;

    protected ContextVariable(T value) {
        this.value = value;
    }

    public abstract String toPromptString();

    public T getValue() {
        return value;
    }

    public abstract ContextVariable<T> append(ContextVariable<?> content);

    public boolean isEmpty() {
        return value == null || value.toString().isEmpty();
    }

    public abstract ContextVariable<T> cloneVariable();


    private static Map<Class<?>, Converter<?>> converters = new HashMap<>();

    private static class Converter<T> {

        private final Function<T, ContextVariable<T>> convert;
        private final Class<T> clazz;

        public Converter(Class<T> clazz, Function<T, ContextVariable<T>> converter) {
            this.clazz = clazz;
            this.convert = converter;
        }

        public ContextVariable<T> convert(Object s) {
            if (s != null && clazz.isAssignableFrom(s.getClass())) {
                return convert.apply((T) s);
            } else {
                return null;
            }
        }
    }

    static {
        putConverter(new Converter<>(ContextVariable.class, x -> x));

        putConverter(new Converter<>(Boolean.class, BooleanVariable::new));
        putConverter(new Converter<>(boolean.class, BooleanVariable::new));

        putConverter(new Converter<>(Number.class, NumberVariable::new));
        putConverter(new Converter<>(byte.class, NumberVariable::new));
        putConverter(new Converter<>(int.class, NumberVariable::new));
        putConverter(new Converter<>(long.class, NumberVariable::new));
        putConverter(new Converter<>(double.class, NumberVariable::new));
        putConverter(new Converter<>(float.class, NumberVariable::new));
        putConverter(new Converter<>(short.class, NumberVariable::new));

        putConverter(new Converter<>(String.class, StringVariable::new));

        putConverter(new Converter<>(ChatHistory.class, ChatHistoryVariable::new));

        putConverter(new Converter<>(Character.class, CharacterVariable::new));
        putConverter(new Converter<>(char.class, CharacterVariable::new));
    }

    private static void putConverter(Converter<?> converter) {
        converters.put(converter.clazz, converter);
    }

    public static ContextVariable<?> of(Object s) {
        Converter<?> converter = converters.get(s.getClass());
        if (converter != null) {
            ContextVariable<?> converted = converter.convert(s);
            if (converted != null) {
                return converted;
            }
        }

        return converters.values().stream()
            .map(c -> c.convert(s))
            .filter(Objects::nonNull)
            .findFirst()
            .orElseThrow(
                () -> new RuntimeException("Unknown context variable type: " + s.getClass()));
    }
}
