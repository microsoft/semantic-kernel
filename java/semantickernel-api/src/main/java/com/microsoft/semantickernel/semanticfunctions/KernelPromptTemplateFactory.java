package com.microsoft.semantickernel.semanticfunctions;

import com.microsoft.semantickernel.templateengine.handlebars.HandlebarsPromptTemplate;
import com.microsoft.semantickernel.templateengine.semantickernel.DefaultPromptTemplate;
import java.util.Locale;

public class KernelPromptTemplateFactory implements PromptTemplateFactory {

    public PromptTemplate tryCreate(PromptTemplateConfig templateConfig) {
        if (templateConfig == null || templateConfig.getTemplateFormat() == null) {
            return new DefaultPromptTemplate(templateConfig);
        }

        switch (templateConfig.getTemplateFormat().toLowerCase(Locale.ROOT)) {
            case "semantic-kernel":
                return new DefaultPromptTemplate(templateConfig);
            case "handlebars":
                return new HandlebarsPromptTemplate(templateConfig);
            default:
                throw new UnknownTemplateFormatException(templateConfig.getTemplateFormat());
        }
    }

    public static class UnknownTemplateFormatException extends IllegalArgumentException {

        public UnknownTemplateFormatException(String templateFormat) {
            super("Unknown template format: " + templateFormat);
        }
    }
}
