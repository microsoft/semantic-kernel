// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.textcompletion;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.SemanticFunctionDefinition;

import java.util.function.Function;

public abstract class CompletionFunctionDefinition
        extends SemanticFunctionDefinition<
                CompletionRequestSettings, CompletionSKContext, CompletionSKFunction> {
    public static CompletionFunctionDefinition of(Function<Kernel, CompletionSKFunction> func) {
        return new CompletionFunctionDefinition() {
            @Override
            protected CompletionSKFunction build(Kernel kernel) {
                return func.apply(kernel);
            }
        };
    }
}
