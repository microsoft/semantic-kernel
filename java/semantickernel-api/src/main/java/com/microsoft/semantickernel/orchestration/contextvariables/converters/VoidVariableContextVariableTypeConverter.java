package com.microsoft.semantickernel.orchestration.contextvariables.converters;

import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter;

public class VoidVariableContextVariableTypeConverter extends
    ContextVariableTypeConverter<Void> {

    public VoidVariableContextVariableTypeConverter() {
        super(
            Void.class,
            s -> null,
            s -> null,
            s -> null);
    }

}
