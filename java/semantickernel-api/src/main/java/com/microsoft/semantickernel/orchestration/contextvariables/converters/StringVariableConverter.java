package com.microsoft.semantickernel.orchestration.contextvariables.converters;

import com.microsoft.semantickernel.orchestration.contextvariables.Converter;

import static com.microsoft.semantickernel.orchestration.contextvariables.VariableTypes.convert;

public class StringVariableConverter extends Converter<String> {

    public StringVariableConverter() {
        super(
            String.class,
            s -> convert(s, String.class),
            Object::toString,
            s -> s);
    }
}
