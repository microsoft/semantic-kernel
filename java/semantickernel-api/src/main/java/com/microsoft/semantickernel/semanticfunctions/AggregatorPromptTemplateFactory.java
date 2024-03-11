// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

import java.util.ArrayList;
import java.util.List;
import reactor.util.annotation.NonNull;

/**
 * An collection of {@link PromptTemplateFactory} instances. The factory will try to create a
 * {@link PromptTemplate} using each factory in the collection until one is successful.
 */
public class AggregatorPromptTemplateFactory implements PromptTemplateFactory {

    private final List<PromptTemplateFactory> templateFactories;

    /**
     * Creates a new instance of {@link AggregatorPromptTemplateFactory}.
     *
     * @param templateFactories the factories to aggregate
     */
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
