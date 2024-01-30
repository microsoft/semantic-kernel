package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.builders.SemanticKernelBuilder;
import com.microsoft.semantickernel.hooks.KernelHooks;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableType;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter.NoopConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes;

import javax.annotation.CheckForNull;
import javax.annotation.Nullable;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
/**
 * Context passed to a Kernel or KernelFunction invoke
 */
public class InvocationContext implements Buildable {

    private final KernelFunctionArguments arguments;
    private final ContextVariableType<?> functionReturnType;
    private final KernelHooks hooks;
    private final PromptExecutionSettings promptExecutionSettings;

    public InvocationContext(
        KernelFunctionArguments arguments,
        ContextVariableType<?> functionReturnType,
        @Nullable
        KernelHooks hooks,
        @Nullable
        PromptExecutionSettings promptExecutionSettings) {
        this.arguments = arguments;
        this.functionReturnType = functionReturnType;
        this.hooks = hooks;
        this.promptExecutionSettings = promptExecutionSettings;
    }

    public KernelFunctionArguments getKernelFunctionArguments() {
        return arguments;
    }

    public ContextVariableType<?> getFunctionReturnType() {
        return functionReturnType;
    }

    @CheckForNull
    public KernelHooks getKernelHooks() {
        return hooks;
    }

    @CheckForNull
    public PromptExecutionSettings getPromptExecutionSettings() {
        return promptExecutionSettings;
    }

    public static Builder builder() {
        return new Builder();
    }

    public static class Builder implements SemanticKernelBuilder<InvocationContext> {

        private static Logger LOGGER = LoggerFactory.getLogger(Builder.class);

        private KernelFunctionArguments arguments;
        private ContextVariableType<?> functionReturnType;
        private KernelHooks hooks;
        private PromptExecutionSettings promptExecutionSettings;

        public Builder withKernelFunctionArguments(KernelFunctionArguments arguments) {
            this.arguments = arguments;
            return this;
        }

        public Builder withFunctionReturnType(ContextVariableType<?> functionReturnType) {
            this.functionReturnType = functionReturnType;
            return this;
        }

        public Builder withFunctionReturnType(Class<?> functionReturnType) {  
            // TODO: javadoc @throws SKException if no default variable type is found
            ContextVariableType<?> contextVariable = ContextVariableTypes.getDefaultVariableTypeForClass(functionReturnType);
            return withFunctionReturnType(contextVariable);
        }

        public Builder withKernelHooks(KernelHooks hooks) {
            this.hooks = hooks;
            return this;
        }

        public Builder withPromptExecutionSettings(PromptExecutionSettings promptExecutionSettings) {
            this.promptExecutionSettings = promptExecutionSettings;
            return this;
        }

        @Override
        public InvocationContext build() {
            if (arguments == null) {
                LOGGER.warn("InvocationContext created without arguments. Defaulting to empty arguments.");
                arguments = new KernelFunctionArguments();
            }
            if (functionReturnType == null) {
                LOGGER.warn("InvocationContext created without functionReturnType. Defaulting to String.");
                functionReturnType = ContextVariableTypes.getDefaultVariableTypeForClass(String.class);
            }
            return new InvocationContext(arguments, functionReturnType, hooks, promptExecutionSettings);
        }
    }
    
}
