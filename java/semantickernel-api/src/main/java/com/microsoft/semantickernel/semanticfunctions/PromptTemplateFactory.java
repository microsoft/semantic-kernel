package com.microsoft.semantickernel.semanticfunctions;

import javax.annotation.Nullable;

public interface PromptTemplateFactory {

    PromptTemplate tryCreate(PromptTemplateConfig templateConfig);

    static PromptTemplate build(PromptTemplateConfig templateConfig) {
        return new KernelPromptTemplateFactory().tryCreate(templateConfig);
    }

    class UnknownTemplateFormatException extends IllegalArgumentException {

        public UnknownTemplateFormatException(@Nullable String templateFormat) {
            super("Unknown template format: " + templateFormat);
        }
    }
}
