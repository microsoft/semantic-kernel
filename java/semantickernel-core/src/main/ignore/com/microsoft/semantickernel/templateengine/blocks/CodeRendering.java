// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine.blocks;

import com.microsoft.semantickernel.orchestration.SKContext;
import reactor.core.publisher.Mono;

/** Interface of dynamic blocks that need async IO to be rendered. */
public interface CodeRendering {
    /**
     * Render the block using the given context, potentially using external I/O.
     *
     * @param context SK execution context
     * @return Rendered content
     */
    Mono<String> renderCodeAsync(SKContext context);
}
