package com.microsoft.semantickernel.orchestration.contextvariables.converters;

import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter;

import java.time.Instant;
import java.time.OffsetDateTime;

/**
 * A {@link ContextVariableTypeConverter} for {@link Instant}.
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
