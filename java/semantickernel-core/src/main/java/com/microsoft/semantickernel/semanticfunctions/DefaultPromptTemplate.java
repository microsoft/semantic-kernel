// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.skilldefinition.ParameterView;
import com.microsoft.semantickernel.templateengine.PromptTemplateEngine;

import reactor.core.publisher.Mono;

import java.util.ArrayList;
import java.util.List;

/// <summary>
/// Prompt template.
/// </summary>
public class DefaultPromptTemplate implements PromptTemplate {
    private final String promptTemplate;
    private final PromptTemplateConfig config;

    public DefaultPromptTemplate(String promptTemplate, PromptTemplateConfig config) {
        this.promptTemplate = promptTemplate;
        this.config = config;
    }

    @Override
    public List<ParameterView> getParameters() {
        return new ArrayList<>();
    }

    @Override
    public Mono<String> renderAsync(
            SKContext executionContext, PromptTemplateEngine promptTemplateEngine) {
        return promptTemplateEngine.renderAsync(this.promptTemplate, executionContext);
    }

    public static final class Builder extends PromptTemplate.Builder {
        @Override
        public PromptTemplate build(String promptTemplate, PromptTemplateConfig config) {
            return new DefaultPromptTemplate(promptTemplate, config);
        }
    }
}
