// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration.planner; // Copyright (c) Microsoft. All rights
// reserved.

import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.orchestration.DefaultCompletionSKContext;
import com.microsoft.semantickernel.orchestration.DefaultCompletionSKFunction;
import com.microsoft.semantickernel.orchestration.DefaultSemanticSKFunction;
import com.microsoft.semantickernel.orchestration.ReadOnlyContextVariables;
import com.microsoft.semantickernel.planner.SequentialPlannerFunctionDefinition;
import com.microsoft.semantickernel.planner.SequentialPlannerSKContext;
import com.microsoft.semantickernel.planner.SequentialPlannerSKFunction;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;
import com.microsoft.semantickernel.textcompletion.CompletionFunctionDefinition;

import reactor.core.publisher.Mono;

import java.util.List;
import java.util.function.Supplier;

import javax.annotation.Nullable;

/// <summary>
/// Standard Semantic Kernel callable function.
/// SKFunction is used to extend one C# <see cref="Delegate"/>, <see cref="Func{T, TResult}"/>, <see
// cref="Action"/>,
/// with additional methods required by the kernel.
/// </summary>
public class DefaultSequentialPlannerSKFunction
        extends DefaultSemanticSKFunction<Void, SequentialPlannerSKContext>
        implements SequentialPlannerSKFunction {

    private final DefaultCompletionSKFunction delegate;

    public DefaultSequentialPlannerSKFunction(DefaultCompletionSKFunction func) {
        super(
                func.getDelegateType(),
                func.getParameters(),
                func.getSkillName(),
                func.getName(),
                func.getDescription(),
                func.getSkillCollection());

        this.delegate = func;
    }

    public static SequentialPlannerFunctionDefinition createFunction(
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
        CompletionFunctionDefinition delegateBuilder =
                DefaultCompletionSKFunction.createFunction(
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
        return SequentialPlannerFunctionDefinition.of(
                (kernel) -> {
                    DefaultCompletionSKFunction inst =
                            (DefaultCompletionSKFunction) delegateBuilder.registerOnKernel(kernel);
                    return new DefaultSequentialPlannerSKFunction(inst);
                });
    }

    @Override
    public Class<Void> getType() {
        return Void.class;
    }

    @Override
    public SequentialPlannerSKContext buildContext(
            ReadOnlyContextVariables variables,
            @Nullable SemanticTextMemory memory,
            @Nullable Supplier<ReadOnlySkillCollection> skills) {
        return new DefaultSequentialPlannerSKContext(variables, memory, skills);
    }

    @Override
    protected Mono<SequentialPlannerSKContext> invokeAsyncInternal(
            SequentialPlannerSKContext context, @Nullable Void settings) {

        return delegate.invokeAsync(
                        new DefaultCompletionSKContext(
                                context.getVariables(),
                                context.getSemanticMemory(),
                                context::getSkills),
                        null)
                .map(
                        res -> {
                            return new DefaultSequentialPlannerSKContext(
                                    res.getVariables(), res.getSemanticMemory(), res::getSkills);
                        });
    }
}
