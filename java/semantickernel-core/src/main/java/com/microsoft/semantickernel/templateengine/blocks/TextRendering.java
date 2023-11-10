// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine.blocks;

import com.microsoft.semantickernel.orchestration.ContextVariables;
import javax.annotation.Nullable;

/// <summary>
/// Interface of static blocks that don't need async IO to be rendered.
/// </summary>
public interface TextRendering {
    /// <summary>
    /// Render the block using only the given variables.
    /// </summary>
    /// <param name="variables">Optional variables used to render the block</param>
    /// <returns>Rendered content</returns>
    @Nullable
    String render(ContextVariables variables);
}
