package com.microsoft.semantickernel.hooks;

import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.KernelFunctionArguments;

import javax.annotation.Nullable;

import edu.umd.cs.findbugs.annotations.SuppressFBWarnings;

/**
 * Represents a KernelHookEvent that is raised after a prompt is rendered.
 */
public class PromptRenderedEvent implements KernelHookEvent {

    private final KernelFunction<?> function;
    private final KernelFunctionArguments arguments;
    private final String prompt;

    /**
     * Creates a new instance of the {@link PromptRenderedEvent} class.
     * @param function the function
     * @param arguments the arguments
     * @param prompt the prompt
     */
    public PromptRenderedEvent(
        KernelFunction function,
        @Nullable
        KernelFunctionArguments arguments,
        String prompt) {
        this.function = function;
        this.arguments = arguments != null ? new KernelFunctionArguments(arguments)
            : new KernelFunctionArguments();
        this.prompt = prompt;
    }

    /**
     * Gets the function that was invoked.
     * @return the function
     */
    public KernelFunction getFunction() {
        return function;
    }

    /**
     * Gets the arguments that were passed to the function.
     * @return the arguments
     */
    @SuppressFBWarnings("EI_EXPOSE_REP")
    public KernelFunctionArguments getArguments() {
        return arguments;
    }

    /**
     * Gets the prompt that was rendered.
     * @return the prompt
     */
    @SuppressFBWarnings("EI_EXPOSE_REP")
    public String getPrompt() {
        return prompt;
    }
}