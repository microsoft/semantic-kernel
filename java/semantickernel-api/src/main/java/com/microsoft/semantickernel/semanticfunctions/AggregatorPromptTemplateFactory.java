package com.microsoft.semantickernel.semanticfunctions;

import java.util.ArrayList;
import java.util.List;
import reactor.util.annotation.NonNull;

public class AggregatorPromptTemplateFactory implements PromptTemplateFactory {

    private final List<PromptTemplateFactory> templateFactories;

    public AggregatorPromptTemplateFactory(List<PromptTemplateFactory> templateFactories) {
        this.templateFactories = new ArrayList<>(templateFactories);
    }

    @Override
    public PromptTemplate tryCreate(@NonNull PromptTemplateConfig templateConfig) {
        for (PromptTemplateFactory factory : templateFactories) {
            try {
                return factory.tryCreate(templateConfig);
            } catch (UnknownTemplateFormatException ignored) {
                // No-op
            }
        }

        throw new UnknownTemplateFormatException(templateConfig.getTemplateFormat());
    }
}
