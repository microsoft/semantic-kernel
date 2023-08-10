// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.textcompletion;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.builders.BuildersSingleton;
import com.microsoft.semantickernel.builders.SemanticKernelBuilder;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.orchestration.SKFunction;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.semanticfunctions.SemanticFunctionConfig;
import java.util.List;
import javax.annotation.Nullable;
import reactor.core.publisher.Mono;

/** Semantic function for text completion */
public interface CompletionSKFunction extends SKFunction<CompletionRequestSettings>, Buildable {

    /**
     * Method to aggregate partitioned results of a semantic function.
     *
     * @param partitionedInput Input to aggregate
     * @param context Semantic Kernel context
     * @return Aggregated results
     */
    Mono<SKContext> aggregatePartitionedResultsAsync(
            List<String> partitionedInput, @Nullable SKContext context);

    static Builder builder() {
        return BuildersSingleton.INST.getInstance(CompletionSKFunction.Builder.class);
    }

    /** Builder for completion functions */
    interface Builder extends SemanticKernelBuilder<CompletionSKFunction> {

        Builder withKernel(Kernel kernel);

        Builder setPromptTemplate(String promptTemplate);

        Builder setPromptTemplateConfig(PromptTemplateConfig config);

        Builder setCompletionConfig(PromptTemplateConfig.CompletionConfig completionConfig);

        Builder setSemanticFunctionConfig(SemanticFunctionConfig functionConfig);

        Builder setSkillName(@Nullable String skillName);

        Builder setFunctionName(@Nullable String functionName);

        Builder setDescription(String description);
    }
}
