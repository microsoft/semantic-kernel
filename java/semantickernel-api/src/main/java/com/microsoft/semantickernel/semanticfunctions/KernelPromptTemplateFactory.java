package com.microsoft.semantickernel.semanticfunctions;

import com.microsoft.semantickernel.templateengine.handlebars.HandlebarsPromptTemplate;
import com.microsoft.semantickernel.templateengine.semantickernel.DefaultPromptTemplate;
import java.util.Locale;

public class KernelPromptTemplateFactory implements PromptTemplateFactory {

    @Override
    public PromptTemplate tryCreate(PromptTemplateConfig templateConfig) {
        switch (templateConfig.getTemplateFormat().toLowerCase(Locale.ROOT)) {
            case "semantic-kernel":
                return new DefaultPromptTemplate(templateConfig);
            case "handlebars":
                return new HandlebarsPromptTemplate(templateConfig);
            default:
                throw new IllegalArgumentException(
                    "Unknown template format: " + templateConfig.getTemplateFormat());
        }
    }
}
