// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.contextvariables.converters;

import static com.microsoft.semantickernel.contextvariables.ContextVariableTypes.convert;

import com.microsoft.semantickernel.contextvariables.ContextVariable;
import com.microsoft.semantickernel.contextvariables.ContextVariableTypeConverter;
import com.microsoft.semantickernel.contextvariables.ContextVariableTypes;
import java.util.Collection;
import java.util.stream.Collectors;

/**
 * A {@link ContextVariableTypeConverter} for {@code java.util.Collection} variables. Use
 * {@code ContextVariableTypes.getGlobalVariableTypeForClass(String.class)} to get an instance of
 * this class.
 *
 * @see ContextVariableTypes#getGlobalVariableTypeForClass(Class)
 */
public class CollectionVariableContextVariableTypeConverter extends
    ContextVariableTypeConverter<Collection> {

    /**
     * Creates a new instance of the {@link CollectionVariableContextVariableTypeConverter} class.
     */
    public CollectionVariableContextVariableTypeConverter() {
        super(
            Collection.class,
            s -> convert(s, Collection.class),
            CollectionVariableContextVariableTypeConverter::getString,
            s -> {
                throw new UnsupportedOperationException();
            });
    }

    private static String getString(Collection<?> c) {
        return c.stream()
            .map(t -> {
                if (t instanceof ContextVariable) {
                    return ((ContextVariable<?>) t).toPromptString();
                } else {
                    return t.toString();
                }
            })
            .collect(Collectors.joining(","));
    }
}
