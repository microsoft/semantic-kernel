// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.textcompletion;

import com.microsoft.semantickernel.builders.BuildersSingleton;
import com.microsoft.semantickernel.orchestration.SKFunction;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.semanticfunctions.SemanticFunctionConfig;

import javax.annotation.Nullable;

public interface CompletionSKFunction
        extends SKFunction<CompletionRequestSettings, CompletionSKContext> {

    static CompletionSKFunction.Builder builder() {
        return BuildersSingleton.INST.getFunctionBuilders().completionBuilders(null);
    }

    interface Builder {
        CompletionSKFunction createFunction(
                String promptTemplate,
                PromptTemplateConfig config,
                String functionName,
                @Nullable String skillName);

        CompletionSKFunction createFunction(
                String functionName, SemanticFunctionConfig functionConfig);

        CompletionSKFunction createFunction(
                @Nullable String skillNameFinal,
                String functionName,
                SemanticFunctionConfig functionConfig);

        CompletionSKFunction createFunction(
                String promptTemplate,
                @Nullable String functionName,
                @Nullable String skillName,
                @Nullable String description);

        CompletionSKFunction createFunction(
                String prompt,
                @Nullable String functionName,
                @Nullable String skillName,
                @Nullable String description,
                PromptTemplateConfig.CompletionConfig completionConfig);
    }
}
