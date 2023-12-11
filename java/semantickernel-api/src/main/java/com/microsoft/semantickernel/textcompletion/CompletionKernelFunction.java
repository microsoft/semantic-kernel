// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.textcompletion;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.builders.BuildersSingleton;
import com.microsoft.semantickernel.builders.SemanticKernelBuilder;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.semanticfunctions.PromptConfig;
import com.microsoft.semantickernel.semanticfunctions.SemanticFunctionConfig;
import java.util.List;
import javax.annotation.Nullable;
import reactor.core.publisher.Mono;

/** Semantic function for text completion */
public interface CompletionKernelFunction extends KernelFunction, Buildable {

    /**
     * Method to aggregate partitioned results of a semantic function.
     *
     * @param partitionedInput Input to aggregate
     * @param context Semantic Kernel context
     * @return Aggregated results
     */
    @Deprecated
    Mono<SKContext> aggregatePartitionedResultsAsync(
            List<String> partitionedInput, @Nullable SKContext context);

    static Builder builder() {
        return BuildersSingleton.INST.getInstance(CompletionKernelFunction.Builder.class);
    }

    /** Builder for completion functions */
    interface Builder extends SemanticKernelBuilder<CompletionKernelFunction> {

        Builder withKernel(Kernel kernel);

        Builder withPromptTemplate(String promptTemplate);

        Builder withPromptTemplateConfig(PromptConfig config);

        Builder withCompletionConfig(PromptConfig.CompletionConfig completionConfig);

        Builder withSemanticFunctionConfig(SemanticFunctionConfig functionConfig);

        Builder withSkillName(@Nullable String skillName);

        Builder withFunctionName(@Nullable String functionName);

        Builder withDescription(String description);
    }
}
