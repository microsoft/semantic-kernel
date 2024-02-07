package com.microsoft.semantickernel.orchestration.contextvariables;

import com.microsoft.semantickernel.exceptions.SKException;
import com.microsoft.semantickernel.orchestration.contextvariables.converters.BooleanVariableContextVariableTypeConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.converters.CharacterVariableContextVariableTypeConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.converters.ChatHistoryVariableContextVariableTypeConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.converters.CompletionUsageContextVariableTypeConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.converters.DateTimeContextVariableTypeConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.converters.InstantContextVariableTypeConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.converters.NumberVariableContextVariableTypeConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.converters.StringVariableContextVariableTypeConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.converters.VoidVariableContextVariableTypeConverter;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import javax.annotation.Nullable;

public class ContextVariableTypes {

    private static final ContextVariableTypes DEFAULT_TYPES;

    static {
        List<ContextVariableTypeConverter<?>> types = Arrays.asList(
            new CharacterVariableContextVariableTypeConverter(),
            new BooleanVariableContextVariableTypeConverter(),
            new ChatHistoryVariableContextVariableTypeConverter(),
            new StringVariableContextVariableTypeConverter(),
            new VoidVariableContextVariableTypeConverter(),
            new ContextVariableTypeConverter<>(void.class, s -> null, s -> null, s -> null),
            new DateTimeContextVariableTypeConverter(),
            new InstantContextVariableTypeConverter(),
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


    private final Map<Class<?>, ContextVariableType<?>> variableTypes;

    public ContextVariableTypes(List<ContextVariableTypeConverter<?>> converters) {
        variableTypes = new HashMap<>();
        converters.forEach(this::putConverter);
    }

    public ContextVariableTypes() {
        variableTypes = new HashMap<>();
    }

    public ContextVariableTypes(ContextVariableTypes contextVariableTypes) {
        this.variableTypes = new HashMap<>(contextVariableTypes.variableTypes);
    }

    public static void addGlobalConverter(
        ContextVariableTypeConverter<?> type) {
        DEFAULT_TYPES.putConverter(type);
    }

    public static <T> ContextVariableType<T> getGlobalVariableTypeForClass(Class<T> aClass) {
        return DEFAULT_TYPES.getVariableTypeForClass(aClass);
    }

    public <T> void putConverter(
        ContextVariableTypeConverter<T> contextVariableTypeConverter) {
        variableTypes.put(contextVariableTypeConverter.getType(),
            new ContextVariableType<>(contextVariableTypeConverter,
                contextVariableTypeConverter.getType()));
    }

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


    @SuppressWarnings("unchecked")
    public <T> ContextVariableType<T> getVariableTypeForClass(Class<T> aClass) {
        try {
            return this.getVariableTypeForClassInternal(aClass);
        } catch (Exception e) {
            return DEFAULT_TYPES.getVariableTypeForClassInternal(aClass);
        }
    }

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

}