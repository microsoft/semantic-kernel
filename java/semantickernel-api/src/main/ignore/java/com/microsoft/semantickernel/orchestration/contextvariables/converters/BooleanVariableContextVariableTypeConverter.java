package com.microsoft.semantickernel.orchestration.contextvariables.converters;

import static com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes.convert;

import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter;

public class BooleanVariableContextVariableTypeConverter extends
    ContextVariableTypeConverter<Boolean> {

    public BooleanVariableContextVariableTypeConverter() {
        super(
            Boolean.class,
            s -> convert(s, Boolean.class),
            Object::toString,
            Boolean::parseBoolean);
    }

}
