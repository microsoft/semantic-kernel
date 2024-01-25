package com.microsoft.semantickernel.orchestration.contextvariables;

import com.microsoft.semantickernel.orchestration.contextvariables.converters.BooleanVariableContextVariableTypeConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.converters.CharacterVariableContextVariableTypeConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.converters.ChatHistoryVariableContextVariableTypeConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.converters.CompletionUsageContextVariableTypeConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.converters.DateTimeContextVariableTypeConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.converters.NumberVariableContextVariableTypeConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.converters.StringVariableContextVariableTypeConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.converters.VoidVariableContextVariableTypeConverter;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class ContextVariableTypes {

    public static final ContextVariableTypes DEFAULT_TYPES;

    static {
        List<ContextVariableTypeConverter<?>> types = Arrays.asList(
            new CharacterVariableContextVariableTypeConverter(),
            new BooleanVariableContextVariableTypeConverter(),
            new ChatHistoryVariableContextVariableTypeConverter(),
            new StringVariableContextVariableTypeConverter(),
            new VoidVariableContextVariableTypeConverter(),
            new DateTimeContextVariableTypeConverter(),
            new CompletionUsageContextVariableTypeConverter(),

            new NumberVariableContextVariableTypeConverter<>(Byte.class, Byte::parseByte),
            new NumberVariableContextVariableTypeConverter<>(byte.class, Byte::parseByte),

            new NumberVariableContextVariableTypeConverter<>(Integer.class, Integer::parseInt),

            new NumberVariableContextVariableTypeConverter<>(int.class, Integer::parseInt),
            new NumberVariableContextVariableTypeConverter<>(Long.class, Long::parseLong),
            new NumberVariableContextVariableTypeConverter<>(long.class, Long::parseLong),

            new NumberVariableContextVariableTypeConverter<>(Double.class, Double::parseDouble),

            new NumberVariableContextVariableTypeConverter<>(double.class, Double::parseDouble),

            new NumberVariableContextVariableTypeConverter<>(Float.class, Float::parseFloat),

            new NumberVariableContextVariableTypeConverter<>(float.class, Float::parseFloat),

            new NumberVariableContextVariableTypeConverter<>(Short.class, Short::parseShort),

            new NumberVariableContextVariableTypeConverter<>(short.class, Short::parseShort));
        DEFAULT_TYPES = new ContextVariableTypes(types);
    }


    private final Map<Class<?>, ContextVariableType<?>> variableTypes = new HashMap<>();

    public ContextVariableTypes(List<ContextVariableTypeConverter<?>> converters) {
        converters.forEach(this::putConverter);
    }

    private <T> void putConverter(
        ContextVariableTypeConverter<T> contextVariableTypeConverter) {
        variableTypes.put(contextVariableTypeConverter.getType(),
            new ContextVariableType<>(contextVariableTypeConverter,
                contextVariableTypeConverter.getType()));
    }

    @SuppressWarnings("unchecked")
    public static <T> T convert(Object s, Class<T> clazz) {
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


    public static <T> ContextVariableType<T> getDefaultVariableTypeForClass(Class<T> aClass) {
        return DEFAULT_TYPES.getVariableTypeForClass(aClass);
    }

    public <T> ContextVariableType<T> getVariableTypeForClass(Class<T> aClass) {
        ContextVariableType<?> contextVariableType = variableTypes.get(aClass);

        if (contextVariableType != null) {
            return (ContextVariableType<T>) contextVariableType;
        }

        return (ContextVariableType<T>) variableTypes
            .values()
            .stream()
            .filter(c -> c.getClazz().isAssignableFrom(aClass))
            .findFirst()
            .orElseThrow(
                () -> new RuntimeException("Unknown context variable type: " + aClass.getName()));

    }
}