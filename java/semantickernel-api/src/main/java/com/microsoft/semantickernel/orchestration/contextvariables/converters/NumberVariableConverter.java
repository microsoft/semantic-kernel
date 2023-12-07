package com.microsoft.semantickernel.orchestration.contextvariables.converters;

import com.microsoft.semantickernel.orchestration.contextvariables.Converter;
import java.util.function.Function;

import static com.microsoft.semantickernel.orchestration.contextvariables.VariableTypes.convert;

public class NumberVariableConverter<T extends Number> extends Converter<T> {

    public NumberVariableConverter(Class<T> clazz, Function<String, T> fromPromptString) {
        super(
            clazz,
            s -> convert(s, clazz),
            Number::toString,
            fromPromptString);
    }
}
