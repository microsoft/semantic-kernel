// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.guice;

/**
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.semanticfunctions.PromptConfig;
import com.microsoft.semantickernel.textcompletion.CompletionKernelFunction;
import jakarta.inject.Inject;

public interface CompletionFunctionFactory {

    CompletionKernelFunction createFunction(
            String prompt, String name, PromptConfig.CompletionConfig completionConfig);

    class CompletionFunctionFactoryImpl implements CompletionFunctionFactory {
        @Inject
        private Kernel kernel;

        @Override
        public CompletionKernelFunction createFunction(
                String prompt,
                String name,
                PromptConfig.CompletionConfig completionConfig) {
            return kernel.getSemanticFunctionBuilder()
                    .withPromptTemplate(prompt)
                    .withFunctionName(name)
                    .withCompletionConfig(completionConfig)
                    .build();
        }
    }
}

 **/