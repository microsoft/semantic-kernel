package com.microsoft.semantickernel.orchestration.contextvariables.converters;

import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter;
import static com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes.convert;

/**
 * A {@link ContextVariableTypeConverter} for {@link String}.
 */
public class StringVariableContextVariableTypeConverter extends
    ContextVariableTypeConverter<String> {

    /**
     * Creates a new instance of the {@link StringVariableContextVariableTypeConverter} class.
     */
    public StringVariableContextVariableTypeConverter() {
        super(
            String.class,
            s -> convert(s, String.class),
            Object::toString,
            s -> s);
    }
}
