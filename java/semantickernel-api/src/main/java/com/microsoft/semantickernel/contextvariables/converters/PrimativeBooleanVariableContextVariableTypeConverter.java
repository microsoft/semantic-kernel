// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.contextvariables.converters;

import com.microsoft.semantickernel.contextvariables.ContextVariableTypeConverter;
import com.microsoft.semantickernel.contextvariables.ContextVariableTypes;
import java.util.Locale;

/**
 * A {@link ContextVariableTypeConverter} for {@link Boolean} variables. Use
 * {@code ContextVariableTypes.getDefaultVariableTypeForClass(Boolean.class)} to get an instance of
 * this class.
 *
 * @see ContextVariableTypes#getGlobalVariableTypeForClass(Class)
 */
public class PrimativeBooleanVariableContextVariableTypeConverter extends
    PrimativeVariableContextVariableTypeConverter {

    /**
     * Initializes a new instance of the
     * {@link PrimativeBooleanVariableContextVariableTypeConverter} class.
     */
    public PrimativeBooleanVariableContextVariableTypeConverter() {
        super(
            boolean.class,
            s -> {
                switch (((String) s).toLowerCase(Locale.ROOT).trim()) {
                    case "true":
                    case "on":
                    case "1":
                    case "yes":
                    case "y":
                    case "t":
                    case "enable":
                        return true;
                    case "false":
                    case "off":
                    case "0":
                    case "no":
                    case "n":
                    case "f":
                    case "disable":
                        return false;
                    default:
                        return null;
                }
            },
            s -> {
                if (s instanceof Boolean || boolean.class.isInstance(s)) {
                    return s;
                }
                return null;
            },
            s -> {
                if (s == null) {
                    return null;
                }
                return ((Boolean) s).toString();
            });
    }

}
