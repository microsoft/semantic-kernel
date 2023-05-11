// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.semantickernel.builders.FunctionBuilders;
import com.microsoft.semantickernel.orchestration.DefaultCompletionSKFunction;
import com.microsoft.semantickernel.orchestration.planner.DefaultSequentialPlannerSKFunction;
import com.microsoft.semantickernel.planner.SequentialPlannerFunctionDefinition;
import com.microsoft.semantickernel.planner.SequentialPlannerSKFunction;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.semanticfunctions.SemanticFunctionConfig;
import com.microsoft.semantickernel.textcompletion.CompletionFunctionDefinition;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;

import java.util.List;

import javax.annotation.Nullable;

public class SkFunctionBuilders implements FunctionBuilders {
    public SkFunctionBuilders() {}

    public static final CompletionSKFunction.Builder COMPLETION_BUILDERS =
            new CompletionSKFunction.Builder() {
                @Override
                public CompletionFunctionDefinition createFunction(
                        String promptTemplate,
                        PromptTemplateConfig config,
                        String functionName,
                        @Nullable String skillName) {
                    return DefaultCompletionSKFunction.createFunction(
                            promptTemplate, config, functionName, skillName);
                }

                @Override
                public CompletionFunctionDefinition createFunction(
                        String functionName, SemanticFunctionConfig functionConfig) {
                    return DefaultCompletionSKFunction.createFunction(functionName, functionConfig);
                }

                @Override
                public CompletionFunctionDefinition createFunction(
                        @Nullable String skillNameFinal,
                        String functionName,
                        SemanticFunctionConfig functionConfig) {
                    return DefaultCompletionSKFunction.createFunction(
                            skillNameFinal, functionName, functionConfig);
                }

                @Override
                public CompletionFunctionDefinition createFunction(
                        String promptTemplate,
                        @Nullable String functionName,
                        @Nullable String skillName,
                        @Nullable String description,
                        int maxTokens,
                        double temperature,
                        double topP,
                        double presencePenalty,
                        double frequencyPenalty,
                        @Nullable List<String> stopSequences) {
                    return DefaultCompletionSKFunction.createFunction(
                            promptTemplate,
                            functionName,
                            skillName,
                            description,
                            maxTokens,
                            temperature,
                            topP,
                            presencePenalty,
                            frequencyPenalty,
                            stopSequences);
                }
            };

    public static final SequentialPlannerSKFunction.Builder PANNER_BUILDERS =
            new SequentialPlannerSKFunction.Builder() {
                @Override
                public SequentialPlannerFunctionDefinition createFunction(
                        String promptTemplate,
                        @Nullable String functionName,
                        @Nullable String skillName,
                        @Nullable String description,
                        int maxTokens,
                        double temperature,
                        double topP,
                        double presencePenalty,
                        double frequencyPenalty,
                        @Nullable List<String> stopSequences) {
                    return DefaultSequentialPlannerSKFunction.createFunction(
                            promptTemplate,
                            functionName,
                            skillName,
                            description,
                            maxTokens,
                            temperature,
                            topP,
                            presencePenalty,
                            frequencyPenalty,
                            stopSequences);
                }
            };

    @Override
    public CompletionSKFunction.Builder completionBuilders() {
        return COMPLETION_BUILDERS;
    }

    @Override
    public SequentialPlannerSKFunction.Builder plannerBuilders() {
        return PANNER_BUILDERS;
    }
}
