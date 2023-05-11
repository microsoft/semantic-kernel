// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.textcompletion;

import com.microsoft.semantickernel.builders.BuildersSingleton;
import com.microsoft.semantickernel.orchestration.SKFunction;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.semanticfunctions.SemanticFunctionConfig;

import java.util.List;

import javax.annotation.Nullable;

public interface CompletionSKFunction
        extends SKFunction<CompletionRequestSettings, CompletionSKContext> {

    static CompletionSKFunction.Builder builder() {
        return BuildersSingleton.INST.getFunctionBuilders().completionBuilders();
    }

    interface Builder {
        CompletionFunctionDefinition createFunction(
                String promptTemplate,
                PromptTemplateConfig config,
                String functionName,
                @Nullable String skillName);

        CompletionFunctionDefinition createFunction(
                String functionName, SemanticFunctionConfig functionConfig);

        CompletionFunctionDefinition createFunction(
                @Nullable String skillNameFinal,
                String functionName,
                SemanticFunctionConfig functionConfig);

        CompletionFunctionDefinition createFunction(
                String promptTemplate,
                @Nullable String functionName,
                @Nullable String skillName,
                @Nullable String description,
                int maxTokens,
                double temperature,
                double topP,
                double presencePenalty,
                double frequencyPenalty,
                @Nullable List<String> stopSequences);
    }
}
