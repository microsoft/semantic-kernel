// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.memory.NullMemory;
import com.microsoft.semantickernel.skilldefinition.KernelSkillsSupplier;
import com.microsoft.semantickernel.skilldefinition.ParameterView;

import reactor.core.publisher.Mono;

import java.util.List;

import javax.annotation.Nullable;

/// <summary>
/// Standard Semantic Kernel callable function.
/// SKFunction is used to extend one C# <see cref="Delegate"/>, <see cref="Func{T, TResult}"/>, <see
// cref="Action"/>,
/// with additional methods required by the kernel.
/// </summary>
public abstract class DefaultSemanticSKFunction<RequestConfiguration>
        extends AbstractSkFunction<RequestConfiguration>
        implements SKFunction<RequestConfiguration> {

    public DefaultSemanticSKFunction(
            DelegateTypes delegateType,
            List<ParameterView> parameters,
            String skillName,
            String functionName,
            String description,
            @Nullable KernelSkillsSupplier kernelSkillsSupplier) {
        super(delegateType, parameters, skillName, functionName, description, kernelSkillsSupplier);
    }

    @Override
    public Mono<SKContext> invokeAsync(
            @Nullable String input,
            @Nullable SKContext context,
            @Nullable RequestConfiguration settings) {
        if (context == null) {
            assertSkillSupplierRegistered();
            context =
                    buildContext(
                            SKBuilders.variables().build(),
                            NullMemory.getInstance(),
                            super.getSkillsSupplier().get());
        } else {
            context = context.copy();
        }

        if (input != null) {
            context = context.update(input);
        }

        return this.invokeAsync(context, settings);
    }
}
