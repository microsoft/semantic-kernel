// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.textcompletion;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.SemanticFunctionDefinition;

import java.util.function.Function;

public abstract class CompletionFunctionDefinition
        extends SemanticFunctionDefinition<
                CompletionRequestSettings, CompletionSKContext, CompletionSkFunction> {
    public static CompletionFunctionDefinition of(Function<Kernel, CompletionSkFunction> func) {
        return new CompletionFunctionDefinition() {
            @Override
            protected CompletionSkFunction build(Kernel kernel) {
                return func.apply(kernel);
            }
        };
    }
}
