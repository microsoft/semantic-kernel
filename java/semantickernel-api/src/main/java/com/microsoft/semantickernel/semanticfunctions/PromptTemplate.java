// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.skilldefinition.ParameterView;
import com.microsoft.semantickernel.templateengine.PromptTemplateEngine;
import java.util.List;
import reactor.core.publisher.Mono;

/** Interface for prompt template */
public interface PromptTemplate {
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

    abstract class Builder {
        protected Builder() {}

        public abstract PromptTemplate build(PromptTemplateEngine promptTemplateEngine);

        public abstract Builder withPromptTemplate(String promptTemplate);

        public abstract Builder withPromptTemplateConfig(PromptTemplateConfig config);
    }
}
