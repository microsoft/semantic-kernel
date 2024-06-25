// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.orchestration.InvocationContext;
import javax.annotation.Nullable;
import reactor.core.publisher.Mono;

/**
 * Represents a prompt template that can be rendered to a string.
 */
public interface PromptTemplate {

    /**
     * Renders the template using the supplied {@code Kernel}, {@code KernelFunctionArguments}, and
     * {@code InvocationContext}.
     *
     * @param kernel    The {@link Kernel} containing services, plugins, and other state for use
     *                  throughout the operation.
     * @param arguments The arguments to use to satisfy any input variables in the prompt template.
     * @param context   The {@link InvocationContext} which carries optional information for the
     *                  prompt rendering.
     * @return The rendered prompt.
     */
    Mono<String> renderAsync(
        Kernel kernel,
        @Nullable KernelFunctionArguments arguments,
        @Nullable InvocationContext context);

}
