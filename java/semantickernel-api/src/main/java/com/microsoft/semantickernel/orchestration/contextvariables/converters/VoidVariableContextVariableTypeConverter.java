package com.microsoft.semantickernel.orchestration.contextvariables.converters;

import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter;

/**
 * A {@link ContextVariableTypeConverter} for {@link Void}.
 */
public class VoidVariableContextVariableTypeConverter extends
    ContextVariableTypeConverter<Void> {

    /**
     * Creates a new instance of the {@link VoidVariableContextVariableTypeConverter} class.
     */
    public VoidVariableContextVariableTypeConverter() {
        super(
            Void.class,
            s -> null,
            s -> null,
            s -> null);
    }

}
