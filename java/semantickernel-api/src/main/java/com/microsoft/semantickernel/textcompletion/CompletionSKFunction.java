// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.textcompletion;

import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.orchestration.SKFunction;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.semanticfunctions.SemanticFunctionConfig;
import java.util.List;
import javax.annotation.Nullable;
import reactor.core.publisher.Mono;

/** Semantic function for text completion */
public interface CompletionSKFunction extends SKFunction<CompletionRequestSettings> {

    /**
     * Method to aggregate partitioned results of a semantic function.
     *
     * @param partitionedInput Input to aggregate
     * @param context Semantic Kernel context
     * @return Aggregated results
     */
    Mono<SKContext> aggregatePartitionedResultsAsync(
            List<String> partitionedInput, @Nullable SKContext context);

    /** Builder for completion functions */
    abstract class Builder {

        protected Builder() {}

        /**
         * Create a new completion function
         *
         * @param promptTemplate Prompt template
         * @param config Prompt template config
         * @param functionName Function name
         * @param skillName Skill name
         * @return Completion function
         */
        public abstract CompletionSKFunction createFunction(
                String promptTemplate,
                PromptTemplateConfig config,
                String functionName,
                @Nullable String skillName);

        /**
         * Create a new completion function
         *
         * @param prompt Prompt
         * @param functionConfig Function config
         * @return Completion function
         */
        public abstract CompletionSKFunction createFunction(
                String prompt, PromptTemplateConfig.CompletionConfig functionConfig);

        /**
         * Create a new completion function
         *
         * @param functionName Function name
         * @param skillName Skill name
         * @return Completion function
         */
        public abstract CompletionSKFunction createFunction(
                @Nullable String skillName,
                String functionName,
                SemanticFunctionConfig functionConfig);

        public abstract CompletionSKFunction createFunction(
                String promptTemplate,
                @Nullable String functionName,
                @Nullable String skillName,
                @Nullable String description);

        public abstract CompletionSKFunction createFunction(
                String prompt,
                @Nullable String functionName,
                @Nullable String skillName,
                @Nullable String description,
                PromptTemplateConfig.CompletionConfig completionConfig);
    }
}
