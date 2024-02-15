package com.microsoft.semantickernel.semanticfunctions;

import com.microsoft.semantickernel.templateengine.handlebars.HandlebarsPromptTemplate;
import java.util.Locale;
import reactor.util.annotation.NonNull;

/**
 * A factory for creating a {@link HandlebarsPromptTemplate} instance for 
 * a {@code PromptTemplateConfig} that uses the handlebars template format.
 */
public class HandlebarsPromptTemplateFactory implements PromptTemplateFactory {

    /**
     * The handlebars template format.
     */
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
