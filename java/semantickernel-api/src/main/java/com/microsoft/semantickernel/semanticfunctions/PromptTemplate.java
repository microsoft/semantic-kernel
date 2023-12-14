// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.builders.BuildersSingleton;
import com.microsoft.semantickernel.builders.SemanticKernelBuilder;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import javax.annotation.Nullable;
import reactor.core.publisher.Mono;

/**
 * Interface for prompt template
 */
public interface PromptTemplate extends Buildable {

    /// <summary>
    /// Render the template using the information in the context
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="arguments">The arguments.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Prompt rendered to string</returns>
    Mono<String> renderAsync(Kernel kernel,
        @Nullable KernelArguments arguments);

    static Builder builder() {
        return BuildersSingleton.INST.getInstance(Builder.class);
    }

    interface Builder extends SemanticKernelBuilder<PromptTemplate> {

        Builder withPromptTemplate(String promptTemplate);

        Builder withPromptTemplateConfig(PromptTemplateConfig config);

    }
}
