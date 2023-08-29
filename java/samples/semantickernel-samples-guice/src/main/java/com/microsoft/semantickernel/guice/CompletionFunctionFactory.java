// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.guice;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;
import jakarta.inject.Inject;

public interface CompletionFunctionFactory {

    CompletionSKFunction createFunction(
            String prompt, String name, PromptTemplateConfig.CompletionConfig completionConfig);

    class CompletionFunctionFactoryImpl implements CompletionFunctionFactory {
        @Inject
        private Kernel kernel;

        @Override
        public CompletionSKFunction createFunction(
                String prompt,
                String name,
                PromptTemplateConfig.CompletionConfig completionConfig) {
            return kernel.getSemanticFunctionBuilder()
                    .withPromptTemplate(prompt)
                    .withFunctionName(name)
                    .withCompletionConfig(completionConfig)
                    .build();
        }
    }
}
