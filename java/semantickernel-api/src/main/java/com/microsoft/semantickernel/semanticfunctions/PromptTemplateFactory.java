package com.microsoft.semantickernel.semanticfunctions;

public interface PromptTemplateFactory {
    PromptTemplate tryCreate(PromptTemplateConfig templateConfig);

    class UnknownTemplateFormatException extends IllegalArgumentException {
        public UnknownTemplateFormatException(String templateFormat) {
            super("Unknown template format: " + templateFormat);
        }
    }
}
