// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.builders.SemanticKernelBuilder;
import com.microsoft.semantickernel.contextvariables.ContextVariableTypeConverter;
import com.microsoft.semantickernel.contextvariables.ContextVariableTypes;
import com.microsoft.semantickernel.hooks.KernelHooks;
import com.microsoft.semantickernel.hooks.KernelHooks.UnmodifiableKernelHooks;
import edu.umd.cs.findbugs.annotations.SuppressFBWarnings;
import javax.annotation.Nullable;

/**
 * Context passed to a Kernel or KernelFunction invoke. This class is primarily for internal use.
 * The preferred way to supply a context is to use the discrete "with" methods in
 * {@link FunctionInvocation}.
 */
public class InvocationContext {

    @Nullable
    private final UnmodifiableKernelHooks hooks;
    @Nullable
    private final PromptExecutionSettings promptExecutionSettings;
    @Nullable
    private final ToolCallBehavior toolCallBehavior;
    private final ContextVariableTypes contextVariableTypes;
    private final InvocationReturnMode invocationReturnMode;

    /**
     * Create a new instance of InvocationContext.
     *
     * @param hooks                   The hooks to use for the invocation.
     * @param promptExecutionSettings The settings for prompt execution.
     * @param toolCallBehavior        The behavior for tool calls.
     * @param contextVariableTypes    The types of context variables.
     */
    protected InvocationContext(
        @Nullable KernelHooks hooks,
        @Nullable PromptExecutionSettings promptExecutionSettings,
        @Nullable ToolCallBehavior toolCallBehavior,
        @Nullable ContextVariableTypes contextVariableTypes,
        InvocationReturnMode invocationReturnMode) {
        this.hooks = unmodifiableClone(hooks);
        this.promptExecutionSettings = promptExecutionSettings;
        this.toolCallBehavior = toolCallBehavior;
        this.invocationReturnMode = invocationReturnMode;
        if (contextVariableTypes == null) {
            this.contextVariableTypes = new ContextVariableTypes();
        } else {
            this.contextVariableTypes = new ContextVariableTypes(contextVariableTypes);
        }
    }

    /**
     * Create a new instance of InvocationContext.
     */
    protected InvocationContext() {
        this.hooks = null;
        this.promptExecutionSettings = null;
        this.toolCallBehavior = null;
        this.contextVariableTypes = new ContextVariableTypes();
        this.invocationReturnMode = InvocationReturnMode.NEW_MESSAGES_ONLY;
    }

    /**
     * Create a new instance of InvocationContext.
     *
     * @param context The context to copy.
     */
    protected InvocationContext(@Nullable InvocationContext context) {
        if (context == null) {
            this.hooks = null;
            this.promptExecutionSettings = null;
            this.toolCallBehavior = null;
            this.contextVariableTypes = new ContextVariableTypes();
            this.invocationReturnMode = InvocationReturnMode.NEW_MESSAGES_ONLY;
        } else {
            this.hooks = context.hooks;
            this.promptExecutionSettings = context.promptExecutionSettings;
            this.toolCallBehavior = context.toolCallBehavior;
            this.contextVariableTypes = context.contextVariableTypes;
            this.invocationReturnMode = context.invocationReturnMode;
        }
    }

    /**
     * Create a new {@link Builder} for building an instance of {@code InvocationContext}.
     *
     * @return the new Builder.
     */
    public static Builder builder() {
        return new Builder();
    }

    @Nullable
    private static UnmodifiableKernelHooks unmodifiableClone(
        @Nullable KernelHooks kernelHooks) {
        if (kernelHooks instanceof UnmodifiableKernelHooks) {
            return (UnmodifiableKernelHooks) kernelHooks;
        } else if (kernelHooks != null) {
            return kernelHooks.unmodifiableClone();
        } else {
            return null;
        }
    }

    /**
     * Create a new instance of InvocationContext by copying the values from another instance.
     *
     * @param context The context to copy.
     * @return The new instance of InvocationContext.
     */
    public static Builder copy(InvocationContext context) {
        return new Builder()
            .withKernelHooks(context.getKernelHooks())
            .withContextVariableConverter(context.contextVariableTypes)
            .withPromptExecutionSettings(context.getPromptExecutionSettings())
            .withToolCallBehavior(context.getToolCallBehavior());
    }

    /**
     * Get the hooks to use for the invocation.
     *
     * @return The hooks to use for the invocation.
     */
    @SuppressFBWarnings(value = "EI_EXPOSE_REP", justification = "returns UnmodifiableKernelHooks")
    @Nullable
    public UnmodifiableKernelHooks getKernelHooks() {
        return hooks;
    }

    /**
     * Get the settings for prompt execution.
     *
     * @return The settings for prompt execution.
     */
    @Nullable
    public PromptExecutionSettings getPromptExecutionSettings() {
        return promptExecutionSettings;
    }

    /**
     * Get the behavior for tool calls.
     *
     * @return The behavior for tool calls.
     */
    @Nullable
    public ToolCallBehavior getToolCallBehavior() {
        return toolCallBehavior;
    }

    /**
     * Get the types of context variables.
     *
     * @return The types of context variables.
     */
    public ContextVariableTypes getContextVariableTypes() {
        return new ContextVariableTypes(contextVariableTypes);
    }

    /**
     * Get the return mode for the invocation.
     *
     * @return this {@link Builder}
     */
    public InvocationReturnMode returnMode() {
        return invocationReturnMode;
    }

    /**
     * Builder for {@link InvocationContext}.
     */
    public static class Builder implements SemanticKernelBuilder<InvocationContext> {

        private final ContextVariableTypes contextVariableTypes = new ContextVariableTypes();
        @Nullable
        private UnmodifiableKernelHooks hooks;
        @Nullable
        private PromptExecutionSettings promptExecutionSettings;
        @Nullable
        private ToolCallBehavior toolCallBehavior;
        private InvocationReturnMode invocationReturnMode = InvocationReturnMode.NEW_MESSAGES_ONLY;

        /**
         * Add kernel hooks to the builder.
         *
         * @param hooks the hooks to add.
         * @return this {@link Builder}
         */
        public Builder withKernelHooks(
            @Nullable KernelHooks hooks) {
            this.hooks = unmodifiableClone(hooks);
            return this;
        }

        /**
         * Add prompt execution settings to the builder.
         *
         * @param promptExecutionSettings the settings to add.
         * @return this {@link Builder}
         */
        public Builder withPromptExecutionSettings(
            @Nullable PromptExecutionSettings promptExecutionSettings) {
            this.promptExecutionSettings = promptExecutionSettings;
            return this;
        }

        /**
         * Add tool call behavior to the builder.
         *
         * @param toolCallBehavior the behavior to add.
         * @return this {@link Builder}
         */
        public Builder withToolCallBehavior(
            @Nullable ToolCallBehavior toolCallBehavior) {
            this.toolCallBehavior = toolCallBehavior;
            return this;
        }

        /**
         * Add a context variable type converter to the builder.
         *
         * @param converter the converter to add.
         * @return this {@link Builder}
         */
        public Builder withContextVariableConverter(ContextVariableTypeConverter<?> converter) {
            this.contextVariableTypes.putConverter(
                converter);
            return this;
        }

        /**
         * Add a context variable type converter to the builder.
         *
         * @param contextVariableTypes the context variable types to add.
         * @return this {@link Builder}
         */
        public Builder withContextVariableConverter(ContextVariableTypes contextVariableTypes) {
            this.contextVariableTypes.putConverters(contextVariableTypes);
            return this;
        }

        /**
         * Set the return mode for the invocation.
         * <p>
         * Defaults to {@link InvocationReturnMode#NEW_MESSAGES_ONLY}.
         *
         * @param invocationReturnMode the return mode for the invocation.
         * @return this {@link Builder}
         */
        public Builder withReturnMode(InvocationReturnMode invocationReturnMode) {
            this.invocationReturnMode = invocationReturnMode;
            return this;
        }

        @Override
        public InvocationContext build() {
            return new InvocationContext(hooks, promptExecutionSettings, toolCallBehavior,
                contextVariableTypes, invocationReturnMode);
        }
    }

}
