// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.implementation.tokenizer.blocks;

import com.microsoft.semantickernel.orchestration.KernelFunctionArguments;
import javax.annotation.Nullable;

/**
 * Interface of static blocks that don't need async IO to be rendered.
 */
public interface TextRendering {

    /**
     * Render the block using only the given variables.
     * @param variables Optional variables used to render the block
     * @return Rendered content
     */
    @Nullable
    String render(@Nullable KernelFunctionArguments variables);
}
