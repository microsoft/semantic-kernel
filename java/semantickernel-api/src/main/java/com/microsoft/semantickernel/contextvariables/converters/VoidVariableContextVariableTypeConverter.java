package com.microsoft.semantickernel.contextvariables.converters;

import com.microsoft.semantickernel.contextvariables.ContextVariableTypeConverter;

/**
 * A {@link com.microsoft.semantickernel.contextvariables.ContextVariableTypeConverter} 
 * for {@code java.lang.Void} types. Use
 * {@code ContextVariableTypes.getGlobalVariableTypeForClass(Void.class)} 
 * to get an instance of this class.
 * @see com.microsoft.semantickernel.contextvariables.ContextVariableTypes#getGlobalVariableTypeForClass(Class)
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
