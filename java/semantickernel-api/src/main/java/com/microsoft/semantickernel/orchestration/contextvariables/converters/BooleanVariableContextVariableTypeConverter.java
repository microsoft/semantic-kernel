package com.microsoft.semantickernel.orchestration.contextvariables.converters;

import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter;
import static com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes.convert;

/**
 * A {@link ContextVariableTypeConverter} for {@link Boolean} variables. Use
 * {@code ContextVariableTypes.getDefaultVariableTypeForClass(Boolean.class)} 
 * to get an instance of this class.
 * @see ContextVariableTypes#getDefaultVariableTypeForClass
 */
public class BooleanVariableContextVariableTypeConverter extends
    ContextVariableTypeConverter<Boolean> {

    /**
     * Initializes a new instance of the {@link BooleanVariableContextVariableTypeConverter} class.
     */
    public BooleanVariableContextVariableTypeConverter() {
        super(
            Boolean.class,
            s -> convert(s, Boolean.class),
            Object::toString,
            Boolean::parseBoolean);
    }

}
