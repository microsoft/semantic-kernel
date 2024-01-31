package com.microsoft.semantickernel.orchestration.contextvariables.converters;

import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter;
import java.time.Instant;
import java.time.OffsetDateTime;
import java.time.ZonedDateTime;
import java.util.Arrays;

public class DateTimeContextVariableTypeConverter extends
    ContextVariableTypeConverter<OffsetDateTime> {

    public DateTimeContextVariableTypeConverter() {
        super(
            OffsetDateTime.class,
            s -> {
                if (s instanceof String) {
                    return ZonedDateTime.parse((String) s).toOffsetDateTime();
                } else if (s instanceof OffsetDateTime) {
                    return (OffsetDateTime) s;
                }
                return null;
            },
            Object::toString,
            o -> {
                return ZonedDateTime.parse(o).toOffsetDateTime();
            },
            Arrays.asList(
                new DefaultConverter<OffsetDateTime, Instant>(OffsetDateTime.class, Instant.class) {
                    @Override
                    public Instant toObject(OffsetDateTime offsetDateTime) {
                        return offsetDateTime.toInstant();
                    }
                }
            ));
    }
}
