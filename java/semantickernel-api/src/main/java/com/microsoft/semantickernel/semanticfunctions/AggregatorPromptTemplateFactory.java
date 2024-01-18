package com.microsoft.semantickernel.semanticfunctions;

import reactor.util.annotation.NonNull;

import java.util.List;

public class AggregatorPromptTemplateFactory implements PromptTemplateFactory {
    private final List<PromptTemplateFactory> templateFactories;
    public AggregatorPromptTemplateFactory(List<PromptTemplateFactory> templateFactories) {
        this.templateFactories = templateFactories;
    }
    @Override
    public PromptTemplate tryCreate(@NonNull PromptTemplateConfig templateConfig) {
        for (PromptTemplateFactory factory : templateFactories) {
            try {
                return factory.tryCreate(templateConfig);
            } catch (UnknownTemplateFormatException ignored) { }
        }

        throw new UnknownTemplateFormatException(templateConfig.getTemplateFormat());
    }
}
