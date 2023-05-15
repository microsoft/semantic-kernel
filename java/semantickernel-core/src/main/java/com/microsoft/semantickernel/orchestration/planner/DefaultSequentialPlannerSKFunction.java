// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration.planner; // Copyright (c) Microsoft. All rights
// reserved.

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.orchestration.ContextVariables;
import com.microsoft.semantickernel.orchestration.DefaultCompletionSKContext;
import com.microsoft.semantickernel.orchestration.DefaultCompletionSKFunction;
import com.microsoft.semantickernel.orchestration.DefaultSemanticSKFunction;
import com.microsoft.semantickernel.planner.SequentialPlannerSKContext;
import com.microsoft.semantickernel.planner.SequentialPlannerSKFunction;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;

import reactor.core.publisher.Mono;

import java.util.List;

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
    private boolean registered = false;

    public DefaultSequentialPlannerSKFunction(DefaultCompletionSKFunction func) {
        super(
                func.getDelegateType(),
                func.getParameters(),
                func.getSkillName(),
                func.getName(),
                func.getDescription(),
                func.getSkillsSupplier());

        this.delegate = func;
    }

    public static DefaultSequentialPlannerSKFunction createFunction(
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
        DefaultCompletionSKFunction delegate =
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

        return new DefaultSequentialPlannerSKFunction(delegate);
    }

    @Override
    public Class<Void> getType() {
        return Void.class;
    }

    @Override
    public SequentialPlannerSKContext buildContext(
            ContextVariables variables,
            @Nullable SemanticTextMemory memory,
            @Nullable ReadOnlySkillCollection skills) {
        return new DefaultSequentialPlannerSKContext(variables, memory, skills);
    }

    @Override
    protected Mono<SequentialPlannerSKContext> invokeAsyncInternal(
            SequentialPlannerSKContext context, @Nullable Void settings) {
        if (!registered) {
            throw new RuntimeException(
                    "It does not appear this function has been registered on a kernel.\n"
                            + "Register it on a kernel either by passing it to"
                            + " KernelConfig.Builder().addSkill() when building the kernel, or\n"
                            + "passing it to Kernel.registerSemanticFunction");
        }

        return delegate.invokeAsync(
                        new DefaultCompletionSKContext(
                                context.getVariables(),
                                context.getSemanticMemory(),
                                context.getSkills()),
                        null)
                .map(
                        res -> {
                            return new DefaultSequentialPlannerSKContext(
                                    res.getVariables(), res.getSemanticMemory(), res.getSkills());
                        });
    }

    @Override
    public void registerOnKernel(Kernel kernel) {
        delegate.registerOnKernel(kernel);
        registered = true;
    }
}
