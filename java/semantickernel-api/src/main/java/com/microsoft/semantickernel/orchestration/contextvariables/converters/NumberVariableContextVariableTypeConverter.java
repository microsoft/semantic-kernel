package com.microsoft.semantickernel.orchestration.contextvariables.converters;

import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter;
import java.util.function.Function;

import static com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes.convert;

public class NumberVariableContextVariableTypeConverter<T extends Number> extends
    ContextVariableTypeConverter<T> {

    public NumberVariableContextVariableTypeConverter(Class<T> clazz, Function<String, T> fromPromptString) {
        super(
            clazz,
            s -> convert(s, clazz),
            Number::toString,
            fromPromptString);
    }
}
