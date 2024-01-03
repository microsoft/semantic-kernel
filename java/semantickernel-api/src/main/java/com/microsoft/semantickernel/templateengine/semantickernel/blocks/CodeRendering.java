// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine.semantickernel.blocks;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
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
     * @return Rendered content
     */
    Mono<String> renderCodeAsync(Kernel kernel, @Nullable KernelArguments arguments);
}
