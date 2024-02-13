package com.microsoft.semantickernel.orchestration.contextvariables.converters;

import com.azure.ai.openai.models.CompletionsUsage;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter;

/**
 * A {@link ContextVariableTypeConverter} for {@link CompletionsUsage}.
 */
public class CompletionUsageContextVariableTypeConverter extends
    ContextVariableTypeConverter<CompletionsUsage> {

    /**
     * Creates a new instance of the {@link CompletionUsageContextVariableTypeConverter} class.
     */
    public CompletionUsageContextVariableTypeConverter() {
        super(
            CompletionsUsage.class,
            s -> {
                if (s instanceof CompletionsUsage) {
                    return (CompletionsUsage) s;
                }
                return null;
            },
            Object::toString,
            o -> null // Do not support parsing from string
        );
    }
}
