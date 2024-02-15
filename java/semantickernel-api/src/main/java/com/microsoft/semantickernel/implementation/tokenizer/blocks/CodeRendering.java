// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.implementation.tokenizer.blocks;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.orchestration.InvocationContext;
import com.microsoft.semantickernel.orchestration.KernelFunctionArguments;

import javax.annotation.Nullable;

import reactor.core.publisher.Mono;

/**
 * Interface of dynamic blocks that need async IO to be rendered.
 */
public interface CodeRendering {

    /**
     * Render the block using the given context, potentially using external I/O.
     *
     * @param kernel    Kernel to use for rendering
     * @param arguments Optional arguments used to render the block
     * @param context   Optional context used to render the block, 
     *                  typically used to pass {code KernelHooks} to the render method.
     * @return Rendered content
     * @see com.microsoft.semantickernel.hooks.KernelHooks
     */
    Mono<String> renderCodeAsync(
        Kernel kernel,
        @Nullable KernelFunctionArguments arguments,
        @Nullable InvocationContext context);
}
