package com.microsoft.semantickernel.semanticfunctions;

import com.microsoft.semantickernel.templateengine.handlebars.HandlebarsPromptTemplate;
import reactor.util.annotation.NonNull;

import java.util.Locale;

public class HandlebarsPromptTemplateFactory implements PromptTemplateFactory {

    public PromptTemplate tryCreate(@NonNull PromptTemplateConfig templateConfig) {
        if (templateConfig.getTemplateFormat() != null &&
                "handlebars".equals(templateConfig.getTemplateFormat().toLowerCase(Locale.ROOT))) {
            return new HandlebarsPromptTemplate(templateConfig);
        }

        throw new UnknownTemplateFormatException(templateConfig.getTemplateFormat());
    }
}
