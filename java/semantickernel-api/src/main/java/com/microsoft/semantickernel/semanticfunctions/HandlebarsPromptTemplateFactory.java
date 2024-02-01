package com.microsoft.semantickernel.semanticfunctions;

import com.microsoft.semantickernel.templateengine.handlebars.HandlebarsPromptTemplate;
import java.util.Locale;
import reactor.util.annotation.NonNull;

public class HandlebarsPromptTemplateFactory implements PromptTemplateFactory {

    public static final String HANDLEBARS_TEMPLATE_FORMAT = "handlebars";

    @Override
    public PromptTemplate tryCreate(@NonNull PromptTemplateConfig templateConfig) {
        if (templateConfig.getTemplateFormat() != null &&
            HANDLEBARS_TEMPLATE_FORMAT.equals(
                templateConfig.getTemplateFormat().toLowerCase(Locale.ROOT))) {
            return new HandlebarsPromptTemplate(templateConfig);
        }

        throw new UnknownTemplateFormatException(templateConfig.getTemplateFormat());
    }
}
