package com.microsoft.semantickernel.contextvariables.converters;

import com.microsoft.semantickernel.contextvariables.ContextVariableTypeConverter;
import com.microsoft.semantickernel.contextvariables.ContextVariableTypes;

import java.time.Instant;
import java.time.OffsetDateTime;

/**
 * A {@link ContextVariableTypeConverter}
 * for {@code java.time.Instant} variables. Use
 * {@code ContextVariableTypes.getGlobalVariableTypeForClass(Instant.class)} 
 * to get an instance of this class.
 * @see ContextVariableTypes#getGlobalVariableTypeForClass(Class)
 */
public class InstantContextVariableTypeConverter extends
    ContextVariableTypeConverter<Instant> {

    /**
     * Creates a new instance of the {@link InstantContextVariableTypeConverter} class.
     */
    public InstantContextVariableTypeConverter() {
        super(
            Instant.class,
            s -> {
                if (s instanceof String) {
                    return Instant.parse((String) s);
                } else if (s instanceof OffsetDateTime) {
                    return ((OffsetDateTime) s).toInstant();
                }
                return null;
            },
            Object::toString,
            o -> {
                return Instant.parse(o);
            });
    }
}
