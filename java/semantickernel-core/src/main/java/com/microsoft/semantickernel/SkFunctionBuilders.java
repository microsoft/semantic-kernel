// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.semantickernel.ai.AIException;
import com.microsoft.semantickernel.builders.FunctionBuilders;
import com.microsoft.semantickernel.orchestration.DefaultCompletionSKFunction;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.semanticfunctions.SemanticFunctionConfig;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;
import javax.annotation.Nullable;

/** Provides various builders for completion functions */
public class SkFunctionBuilders implements FunctionBuilders {
    public SkFunctionBuilders() {}

    private static class InternalCompletionBuilder extends CompletionSKFunction.Builder {
        private final Kernel kernel;

        private InternalCompletionBuilder(Kernel kernel) {
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
                            promptTemplate,
                            config,
                            functionName,
                            skillName,
                            kernel.getPromptTemplateEngine()));
        }

        @Override
        public CompletionSKFunction createFunction(
                String prompt, PromptTemplateConfig.CompletionConfig functionConfig) {
            return createFunction(prompt, null, null, null, functionConfig);
        }

        @Override
        public CompletionSKFunction createFunction(
                @Nullable String skillNameFinal,
                String functionName,
                SemanticFunctionConfig functionConfig) {
            return register(
                    DefaultCompletionSKFunction.createFunction(
                            skillNameFinal,
                            functionName,
                            functionConfig,
                            kernel.getPromptTemplateEngine()));
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
            if (kernel == null) {
                throw new AIException(
                        AIException.ErrorCodes.InvalidConfiguration,
                        "Called builder to create a function that");
            }

            return register(
                    DefaultCompletionSKFunction.createFunction(
                            prompt,
                            functionName,
                            skillName,
                            description,
                            completionConfig,
                            kernel.getPromptTemplateEngine()));
        }
    }

    @Override
    public CompletionSKFunction.Builder completionBuilders(Kernel kernel) {
        return new InternalCompletionBuilder(kernel);
    }
}
