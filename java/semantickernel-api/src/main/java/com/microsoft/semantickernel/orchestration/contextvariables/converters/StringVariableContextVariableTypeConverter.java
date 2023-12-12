package com.microsoft.semantickernel.orchestration.contextvariables.converters;

import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter;

import static com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes.convert;

public class StringVariableContextVariableTypeConverter extends
    ContextVariableTypeConverter<String> {

    public StringVariableContextVariableTypeConverter() {
        super(
            String.class,
            s -> convert(s, String.class),
            Object::toString,
            s -> s);
    }
}
