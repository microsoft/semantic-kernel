// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine.handlebars;

import com.microsoft.semantickernel.orchestration.ContextVariables;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.skilldefinition.ParameterView;
import com.microsoft.semantickernel.templateengine.PromptTemplateEngine;
import java.util.List;
import reactor.core.publisher.Mono;

public class HandlebarsPromptTemplate implements PromptTemplate {
    private String promptTemplate;
    private HandlebarsPromptTemplateEngine templateEngine;

    public HandlebarsPromptTemplate(String promptTemplate, PromptTemplateEngine templateEngine) {
        this.promptTemplate = promptTemplate;
        this.templateEngine = (HandlebarsPromptTemplateEngine) templateEngine;
    }

    @Override
    public List<ParameterView> getParameters() {
        return null;
    }

    @Override
    public Mono<String> renderAsync(SKContext skContext) {
        return null;
    }

    @Override
    public Mono<String> renderAsync(ContextVariables variables) {
        return templateEngine.renderAsync(this.promptTemplate, variables);
    }
}
