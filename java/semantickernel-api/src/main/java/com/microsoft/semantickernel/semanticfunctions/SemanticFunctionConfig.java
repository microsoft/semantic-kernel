// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

/** Semantic function configuration */
public class SemanticFunctionConfig {
    private final PromptTemplateConfig config;

    /** Prompt template */
    private final PromptTemplate template;

    /**
     * Constructor for SemanticFunctionConfig.
     *
     * @param config Prompt template configuration.
     * @param template Prompt template.
     */
    public SemanticFunctionConfig(PromptTemplateConfig config, PromptTemplate template) {
        this.config = config;
        this.template = template;
    }

    public PromptTemplateConfig getConfig() {
        return config;
    }

    public PromptTemplate getTemplate() {
        return template;
    }
}
