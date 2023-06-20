// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.semantickernel.builders.FunctionBuilders;
import com.microsoft.semantickernel.orchestration.DefaultCompletionSKFunction;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.semanticfunctions.SemanticFunctionConfig;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;

import javax.annotation.Nullable;

public class SkFunctionBuilders implements FunctionBuilders {
    public SkFunctionBuilders() {}

    public static final CompletionSKFunction.Builder COMPLETION_BUILDERS =
            new InternalCompletionBuilder(null);

    private static class InternalCompletionBuilder extends CompletionSKFunction.Builder {
        private final @Nullable Kernel kernel;

        private InternalCompletionBuilder(@Nullable Kernel kernel) {
            this.kernel = kernel;
        }

        private DefaultCompletionSKFunction register(DefaultCompletionSKFunction function) {
            if (kernel != null) {
                kernel.registerSemanticFunction(function);
            }
            return function;
        }

        @Override
        public CompletionSKFunction createFunction(
                String promptTemplate,
                PromptTemplateConfig config,
                String functionName,
                @Nullable String skillName) {
            return register(
                    DefaultCompletionSKFunction.createFunction(
                            promptTemplate, config, functionName, skillName));
        }

        @Override
        public CompletionSKFunction createFunction(
                String functionName, SemanticFunctionConfig functionConfig) {
            return register(
                    DefaultCompletionSKFunction.createFunction(functionName, functionConfig));
        }

        @Override
        public CompletionSKFunction createFunction(
                @Nullable String skillNameFinal,
                String functionName,
                SemanticFunctionConfig functionConfig) {
            return register(
                    DefaultCompletionSKFunction.createFunction(
                            skillNameFinal, functionName, functionConfig));
        }

        @Override
        public CompletionSKFunction createFunction(
                String promptTemplate,
                @Nullable String functionName,
                @Nullable String skillName,
                @Nullable String description) {
            return createFunction(
                    promptTemplate,
                    functionName,
                    skillName,
                    description,
                    new PromptTemplateConfig.CompletionConfig());
        }

        @Override
        public CompletionSKFunction createFunction(
                String prompt,
                @Nullable String functionName,
                @Nullable String skillName,
                @Nullable String description,
                PromptTemplateConfig.CompletionConfig completionConfig) {

            return register(
                    DefaultCompletionSKFunction.createFunction(
                            prompt, functionName, skillName, description, completionConfig));
        }
    }

    @Override
    public CompletionSKFunction.Builder completionBuilders(@Nullable Kernel kernel) {
        if (kernel == null) {
            return COMPLETION_BUILDERS;
        } else {
            return new InternalCompletionBuilder(kernel);
        }
    }
}
