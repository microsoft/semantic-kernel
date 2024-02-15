package com.microsoft.semantickernel.orchestration.contextvariables.converters;

import static com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes.convert;

import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter;

/**
 * A {@link com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter} 
 * for {@code java.lang.String} variables. Use
 * {@code ContextVariableTypes.getGlobalVariableTypeForClass(String.class)} 
 * to get an instance of this class.
 * @see com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes#getGlobalVariableTypeForClass(Class)
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
