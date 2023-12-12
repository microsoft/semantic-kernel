// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine.handlebars;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import javax.annotation.Nullable;
import reactor.core.publisher.Mono;

public class HandlebarsPromptTemplate implements PromptTemplate {

    @Nullable
    private PromptTemplateConfig promptTemplate;

    public HandlebarsPromptTemplate() {
        this(null);
    }

    public HandlebarsPromptTemplate(
        @Nullable PromptTemplateConfig promptTemplate) {
        this.promptTemplate = promptTemplate;
    }

    @Override
    public Mono<String> renderAsync(Kernel kernel,
        @Nullable KernelArguments arguments) {
        return null;
    }

    /*
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

     */
}
