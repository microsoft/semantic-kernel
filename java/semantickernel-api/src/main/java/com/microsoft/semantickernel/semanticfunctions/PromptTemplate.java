// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.builders.BuildersSingleton;
import com.microsoft.semantickernel.builders.SemanticKernelBuilder;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.skilldefinition.ParameterView;
import com.microsoft.semantickernel.templateengine.PromptTemplateEngine;
import java.util.List;
import reactor.core.publisher.Mono;

/** Interface for prompt template */
public interface PromptTemplate extends Buildable {
    /**
     * Get the list of parameters required by the template, using configuration and template info
     *
     * @return List of parameters
     */
    List<ParameterView> getParameters();

    /**
     * Render the template using the information in the context
     *
     * @param executionContext Kernel execution context helpers
     * @return Prompt rendered to string
     */
    Mono<String> renderAsync(SKContext executionContext);

    static Builder builder() {
        return BuildersSingleton.INST.getInstance(Builder.class);
    }

    interface Builder extends SemanticKernelBuilder<PromptTemplate> {

        Builder setPromptTemplate(String promptTemplate);

        Builder setPromptTemplateConfig(PromptTemplateConfig config);

        Builder setPromptTemplateEngine(PromptTemplateEngine promptTemplateEngine);
    }
}
