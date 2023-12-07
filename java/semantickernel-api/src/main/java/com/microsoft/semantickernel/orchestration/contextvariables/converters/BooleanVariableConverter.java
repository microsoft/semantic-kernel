package com.microsoft.semantickernel.orchestration.contextvariables.converters;

import com.microsoft.semantickernel.orchestration.contextvariables.Converter;

import static com.microsoft.semantickernel.orchestration.contextvariables.VariableTypes.convert;

public class BooleanVariableConverter extends Converter<Boolean> {

    public BooleanVariableConverter() {
        super(
            Boolean.class,
            s -> convert(s, Boolean.class),
            Object::toString,
            Boolean::parseBoolean);
    }
}
