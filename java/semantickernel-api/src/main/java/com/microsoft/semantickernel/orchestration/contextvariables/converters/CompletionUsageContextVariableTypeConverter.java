package com.microsoft.semantickernel.orchestration.contextvariables.converters;

import com.azure.ai.openai.models.CompletionsUsage;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter;

public class CompletionUsageContextVariableTypeConverter extends
    ContextVariableTypeConverter<CompletionsUsage> {

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
