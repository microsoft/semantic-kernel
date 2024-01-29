package com.microsoft.semantickernel.semanticfunctions;

import static com.microsoft.semantickernel.semanticfunctions.HandlebarsPromptTemplateFactory.HANDLEBARS_TEMPLATE_FORMAT;
import static com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig.SEMANTIC_KERNEL_TEMPLATE_FORMAT;

import com.microsoft.semantickernel.templateengine.handlebars.HandlebarsPromptTemplate;
import com.microsoft.semantickernel.templateengine.semantickernel.DefaultPromptTemplate;
import javax.annotation.Nonnull;
import java.util.Locale;

public class KernelPromptTemplateFactory implements PromptTemplateFactory {

    public PromptTemplate tryCreate(@Nonnull PromptTemplateConfig templateConfig) {
        switch (templateConfig.getTemplateFormat().toLowerCase(Locale.ROOT)) {
            case SEMANTIC_KERNEL_TEMPLATE_FORMAT:
                return new DefaultPromptTemplate(templateConfig);
            case HANDLEBARS_TEMPLATE_FORMAT:
                return new HandlebarsPromptTemplate(templateConfig);
            default:
                throw new UnknownTemplateFormatException(templateConfig.getTemplateFormat());
        }
    }
}
