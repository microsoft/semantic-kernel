// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.contextvariables.converters;

import com.microsoft.semantickernel.contextvariables.ContextVariable;
import com.microsoft.semantickernel.contextvariables.ContextVariableType;
import com.microsoft.semantickernel.contextvariables.ContextVariableTypes;
import java.io.Serializable;
import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.stream.Stream;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.TestFactory;

public class ContextVariableTypeConverterTest {

    @TestFactory
    public Stream<DynamicTest> testConvertIntegerToString() {
        return Stream.of(
            new TestCase<>("StringToInteger", String.class, Integer.class, "1"),
            new TestCase<>("IntegerToString", Integer.class, String.class, 1),

            new TestCase<>("StringToFloat", String.class, Float.class, "0.1"),
            new TestCase<>("FloatToString", Float.class, String.class, 0.1f),

            new TestCase<>("StringToBoolean", String.class, Boolean.class, "true"),
            new TestCase<>("BooleanToString", Boolean.class, String.class, true),

            new TestCase<>("NumberToInteger", Number.class, Integer.class, 100.0f),
            new TestCase<>("IntegerToNumber", Integer.class, Number.class, 100),

            new TestCase<>("StringToDate", String.class, OffsetDateTime.class,
                ZonedDateTime.now(ZoneId.systemDefault()).format(DateTimeFormatter.ISO_DATE_TIME)),
            new TestCase<>("DateToString", OffsetDateTime.class, String.class,
                OffsetDateTime.now(ZoneId.systemDefault())))
            .map(s -> DynamicTest.dynamicTest(s.name, () -> {
                Assertions.assertNotNull(ContextVariable.ofGlobalType(s.object));
                Assertions.assertNotNull(ContextVariable.ofGlobalType(s.object).getValue());

                try {
                    ContextVariableType<? extends Serializable> type = ContextVariableTypes
                        .getGlobalVariableTypeForClass(
                            s.targetClazz);
                    Assertions.assertNotNull(ContextVariable.convert(s.object, type));
                } catch (Exception ignored) {

                }
            }));

    }

    private static class TestCase<T, U> {

        private final String name;
        private final Class<T> clazz;
        private final Class<U> targetClazz;
        private final T object;

        private TestCase(String name, Class<T> clazz, Class<U> targetClazz, T object) {
            this.name = name;
            this.clazz = clazz;
            this.targetClazz = targetClazz;
            this.object = object;
        }
    }

}
