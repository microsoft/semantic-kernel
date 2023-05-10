// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine.blocks; // Copyright (c) Microsoft. All rights
// reserved.

import com.microsoft.semantickernel.orchestration.ReadOnlySKContext;

import java.util.concurrent.FutureTask;

import javax.annotation.Nullable;

/// <summary>
/// Interface of dynamic blocks that need async IO to be rendered.
/// </summary>
public interface CodeRendering {
    /// <summary>
    /// Render the block using the given context, potentially using external I/O.
    /// </summary>
    /// <param name="context">SK execution context</param>
    /// <returns>Rendered content</returns>
    @Nullable
    FutureTask<String> renderCodeAsync(ReadOnlySKContext context);
}
