package com.microsoft.semantickernel.orchestration.contextvariables;

import com.microsoft.semantickernel.orchestration.contextvariables.converters.BooleanVariableConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.converters.CharacterVariableConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.converters.ChatHistoryVariableConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.converters.NumberVariableConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.converters.StringVariableConverter;
import java.util.HashMap;
import java.util.Map;

public class VariableTypes {

    private static Map<Class<?>, VariableType<?>> variableTypes = new HashMap<>();

/*
    public static <T> ContextVariable<T> convert(Object s, Class<T> clazz) {
        if (s != null && clazz.isAssignableFrom(s.getClass())) {
            return convert.apply((T) s);
        } else {
            return null;
        }
    }

 */

    static {
        putConverter(new CharacterVariableConverter());
        putConverter(new BooleanVariableConverter());
        putConverter(new ChatHistoryVariableConverter());
        putConverter(new StringVariableConverter());

        putConverter(new NumberVariableConverter<>(Byte.class, Byte::parseByte));
        putConverter(new NumberVariableConverter<>(byte.class, Byte::parseByte));
        putConverter(new NumberVariableConverter<>(Integer.class, Integer::parseInt));
        putConverter(new NumberVariableConverter<>(int.class, Integer::parseInt));
        putConverter(new NumberVariableConverter<>(Long.class, Long::parseLong));
        putConverter(new NumberVariableConverter<>(long.class, Long::parseLong));
        putConverter(new NumberVariableConverter<>(Double.class, Double::parseDouble));
        putConverter(new NumberVariableConverter<>(double.class, Double::parseDouble));
        putConverter(new NumberVariableConverter<>(Float.class, Float::parseFloat));
        putConverter(new NumberVariableConverter<>(float.class, Float::parseFloat));
        putConverter(new NumberVariableConverter<>(Short.class, Short::parseShort));
        putConverter(new NumberVariableConverter<>(short.class, Short::parseShort));
    }

    private static <T> void putConverter(Converter<T> converter) {
        variableTypes.put(converter.getType(), new VariableType<>(converter, converter.getType()));
    }

    public static <T> T convert(Object s, Class<T> clazz) {
        if (s != null && clazz.isAssignableFrom(s.getClass())) {
            return (T) s;
        } else {
            return null;
        }
    }

    public static <T> VariableType<T> getVariableTypeForClass(Class<T> aClass) {
        VariableType<?> variableType = variableTypes.get(aClass);

        if (variableType != null) {
            return (VariableType<T>) variableType;
        }

        return (VariableType<T>) variableTypes
            .values()
            .stream()
            .filter(c -> c.getClazz().isAssignableFrom(aClass))
            .findFirst()
            .orElseThrow(
                () -> new RuntimeException("Unknown context variable type: " + aClass.getName()));

    }
    /*
    public static ContextVariable<?> of(Object s) {
        Converter<?> converter = converters.get(s.getClass());

        if (converter != null) {
            Object converted = converter.fromObject(s);
            if (converted != null) {
                return converted;
            }
        }

        return converters.values().stream()
            .map(c -> c.fromObject(s))
            .filter(Objects::nonNull)
            .findFirst()
            .orElseThrow(
                () -> new RuntimeException("Unknown context variable type: " + s.getClass()));
    }

     */
}