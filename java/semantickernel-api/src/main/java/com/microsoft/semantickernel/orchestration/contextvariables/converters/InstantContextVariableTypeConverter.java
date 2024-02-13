package com.microsoft.semantickernel.orchestration.contextvariables.converters;

import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter;
import java.time.Instant;
import java.time.OffsetDateTime;

public class InstantContextVariableTypeConverter extends
    ContextVariableTypeConverter<Instant> {

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
