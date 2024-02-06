package com.microsoft.semantickernel.orchestration;

import javax.annotation.Nullable;

import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.builders.SemanticKernelBuilder;
import com.microsoft.semantickernel.hooks.KernelHooks;
import com.microsoft.semantickernel.hooks.KernelHooks.UnmodifiableKernelHooks;
import com.microsoft.semantickernel.orchestration.ToolCallBehavior.UnmodifiableToolCallBehavior;

import edu.umd.cs.findbugs.annotations.SuppressFBWarnings;

/**
 * Context passed to a Kernel or KernelFunction invoke
 */
public class InvocationContext implements Buildable {

    private final UnmodifiableKernelHooks hooks;
    private final PromptExecutionSettings promptExecutionSettings;
    private final UnmodifiableToolCallBehavior toolCallBehavior;

    public InvocationContext(
        @Nullable KernelHooks hooks,
        @Nullable PromptExecutionSettings promptExecutionSettings,
        @Nullable ToolCallBehavior toolCallBehavior) {
        this.hooks = unmodifiableClone(hooks);
        this.promptExecutionSettings = promptExecutionSettings;
        this.toolCallBehavior = unmodifiableClone(toolCallBehavior);
    }

    @SuppressFBWarnings(value="EI_EXPOSE_REP", justification="returns UnmodifiableKernelHooks")
    @Nullable
    public UnmodifiableKernelHooks getKernelHooks() {
        return hooks;
    }

    @Nullable
    public PromptExecutionSettings getPromptExecutionSettings() {
        return promptExecutionSettings;
    }

    @SuppressFBWarnings(value="EI_EXPOSE_REP", justification="returns UnmodifiableToolCallBehavior")
    @Nullable
    public UnmodifiableToolCallBehavior getToolCallBehavior() {
        return toolCallBehavior;
    }

    public static Builder builder() {
        return new Builder();
    }

    private static UnmodifiableToolCallBehavior unmodifiableClone(ToolCallBehavior toolCallBehavior) {
        if (toolCallBehavior instanceof UnmodifiableToolCallBehavior) {
            return (UnmodifiableToolCallBehavior) toolCallBehavior;
        } else if (toolCallBehavior != null) {
            return toolCallBehavior.unmodifiableClone();
        } else {
            return null;
        }
    }

    private static UnmodifiableKernelHooks unmodifiableClone(KernelHooks kernelHooks) {
        if (kernelHooks instanceof UnmodifiableKernelHooks) {
            return (UnmodifiableKernelHooks) kernelHooks;
        } else if (kernelHooks != null) {
            return kernelHooks.unmodifiableClone();
        } else {
            return null;
        }
    }

    public static class Builder implements SemanticKernelBuilder<InvocationContext> {

        private UnmodifiableKernelHooks hooks;
        private PromptExecutionSettings promptExecutionSettings;
        private UnmodifiableToolCallBehavior toolCallBehavior;

        public Builder withKernelHooks(KernelHooks hooks) {
            this.hooks = unmodifiableClone(hooks);
            return this;
        }

        public Builder withPromptExecutionSettings(PromptExecutionSettings promptExecutionSettings) {
            this.promptExecutionSettings = promptExecutionSettings;
            return this;
        }

        public Builder withToolCallBehavior(ToolCallBehavior toolCallBehavior) {
            this.toolCallBehavior = unmodifiableClone(toolCallBehavior);
            return this;
        }

        @Override
        public InvocationContext build() {
            return new InvocationContext(hooks, promptExecutionSettings, toolCallBehavior);
        }
    }
    
}
