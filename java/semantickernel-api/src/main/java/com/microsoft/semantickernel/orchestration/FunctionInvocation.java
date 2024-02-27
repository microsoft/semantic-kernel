// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.contextvariables.ContextVariable;
import com.microsoft.semantickernel.contextvariables.ContextVariableType;
import com.microsoft.semantickernel.contextvariables.ContextVariableTypeConverter;
import com.microsoft.semantickernel.contextvariables.ContextVariableTypes;
import com.microsoft.semantickernel.exceptions.SKException;
import com.microsoft.semantickernel.hooks.KernelHook;
import com.microsoft.semantickernel.hooks.KernelHooks;
import com.microsoft.semantickernel.hooks.KernelHooks.UnmodifiableKernelHooks;
import com.microsoft.semantickernel.orchestration.ToolCallBehavior.UnmodifiableToolCallBehavior;
import com.microsoft.semantickernel.semanticfunctions.KernelFunction;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionArguments;
import edu.umd.cs.findbugs.annotations.SuppressFBWarnings;
import java.util.function.BiConsumer;
import javax.annotation.Nullable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import reactor.core.CoreSubscriber;
import reactor.core.publisher.Mono;
import reactor.core.publisher.SynchronousSink;

/**
 * {@code FunctionInvocation} supports fluent invocation of a function in the kernel.
 *
 * @param <T> The type of the result of the function invocation.
 */
public class FunctionInvocation<T> extends Mono<FunctionResult<T>> {

    private static final Logger LOGGER = LoggerFactory.getLogger(FunctionInvocation.class);

    protected final KernelFunction<?> function;

    protected final Kernel kernel;
    @Nullable
    protected final ContextVariableType<T> resultType;
    protected final ContextVariableTypes contextVariableTypes = new ContextVariableTypes();
    @Nullable
    protected KernelFunctionArguments arguments;
    @Nullable
    protected UnmodifiableKernelHooks hooks;
    @Nullable
    protected PromptExecutionSettings promptExecutionSettings;
    @Nullable
    protected UnmodifiableToolCallBehavior toolCallBehavior;

    private boolean isSubscribed = false;

    /**
     * Create a new function invocation.
     *
     * @param kernel   The kernel to invoke the function on.
     * @param function The function to invoke.
     */
    @SuppressFBWarnings("EI_EXPOSE_REP2")
    public FunctionInvocation(
        Kernel kernel,
        KernelFunction<T> function) {
        this.function = function;
        this.kernel = kernel;
        this.resultType = null;
        this.addKernelHooks(kernel.getGlobalKernelHooks());
    }

    /**
     * Create a new function invocation.
     *
     * @param kernel     The kernel to invoke the function on.
     * @param function   The function to invoke.
     * @param resultType The type of the result of the function invocation.
     */
    @SuppressFBWarnings("EI_EXPOSE_REP2")
    public FunctionInvocation(
        Kernel kernel,
        KernelFunction<?> function,
        @Nullable ContextVariableType<T> resultType) {
        this.function = function;
        this.kernel = kernel;
        this.resultType = resultType;
        if (resultType != null) {
            contextVariableTypes.putConverter(resultType.getConverter());
        }
        this.addKernelHooks(kernel.getGlobalKernelHooks());
    }

    // Extracted to static to ensure mutable state is not used
    private static <T> void performSubscribe(
        CoreSubscriber<? super FunctionResult<T>> coreSubscriber,
        Kernel kernel,
        KernelFunction<?> function,
        @Nullable KernelFunctionArguments arguments,
        @Nullable ContextVariableType<T> variableType,
        @Nullable InvocationContext context) {
        if (variableType == null) {
            LOGGER.debug(
                "No variable type explicitly specified by calling 'withResultType' for function invocation: "
                    + function.getPluginName() + "." + function.getName() + "."
                    + " This may cause a runtime error (probably a ClassCastException) if the result type is not compatible with the expected type.");
        }

        function
            .invokeAsync(
                kernel,
                KernelFunctionArguments.builder().withVariables(arguments).build(),
                null,
                new InvocationContext(context))
            .handle(convertToType(variableType))
            .subscribe(coreSubscriber);
    }

    private static <T> BiConsumer<FunctionResult<?>, SynchronousSink<FunctionResult<T>>> convertToType(
        @Nullable ContextVariableType<T> variableType) {
        return (result, sink) -> {
            // If a specific result type was requested, convert the result to that type.
            if (variableType != null) {
                try {
                    sink.next(new FunctionResult<>(
                        ContextVariable.convert(result.getResult(), variableType),
                        result.getMetadata()));
                } catch (Exception e) {
                    sink.error(new SKException(
                        "Failed to convert result to requested type: "
                            + variableType.getClazz().getName(),
                        e));
                }
            } else {
                // Otherwise, just pass the result through and trust that the user requested the correct type.
                sink.next((FunctionResult<T>) result);
            }
        };
    }

    @Nullable
    private static UnmodifiableToolCallBehavior unmodifiableClone(
        @Nullable ToolCallBehavior toolCallBehavior) {
        if (toolCallBehavior instanceof UnmodifiableToolCallBehavior) {
            return (UnmodifiableToolCallBehavior) toolCallBehavior;
        } else if (toolCallBehavior != null) {
            return toolCallBehavior.unmodifiableClone();
        } else {
            return null;
        }
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
     * Supply arguments to the function invocation.
     *
     * @param arguments The arguments to supply to the function invocation.
     * @return this {@code FunctionInvocation} for fluent chaining.
     */
    public FunctionInvocation<T> withArguments(
        @Nullable KernelFunctionArguments arguments) {
        logSubscribeWarning();
        this.arguments = KernelFunctionArguments.builder().withVariables(arguments).build();
        return this;
    }

    /**
     * Supply the result type of function invocation.
     *
     * @param resultType The arguments to supply to the function invocation.
     * @param <U>        The type of the result of the function invocation.
     * @return A new {@code FunctionInvocation} for fluent chaining.
     */
    public <U> FunctionInvocation<U> withResultType(ContextVariableType<U> resultType) {
        logSubscribeWarning();
        return new FunctionInvocation<>(
            kernel,
            function,
            resultType)
            .withArguments(arguments)
            .addKernelHooks(hooks)
            .withPromptExecutionSettings(promptExecutionSettings)
            .withToolCallBehavior(toolCallBehavior);
    }

    /**
     * Add a kernel hook to the function invocation.
     *
     * @param hook The kernel hook to add.
     * @return this {@code FunctionInvocation} for fluent chaining.
     */
    public FunctionInvocation<T> addKernelHook(@Nullable KernelHook<?> hook) {
        if (hook == null) {
            return this;
        }
        logSubscribeWarning();
        KernelHooks clone = new KernelHooks(this.hooks);
        clone.addHook(hook);
        this.hooks = unmodifiableClone(clone);
        return this;
    }

    /**
     * Add kernel hooks to the function invocation.
     *
     * @param hooks The kernel hooks to add.
     * @return this {@code FunctionInvocation} for fluent chaining.
     */
    public FunctionInvocation<T> addKernelHooks(
        @Nullable KernelHooks hooks) {
        if (hooks == null) {
            return this;
        }
        logSubscribeWarning();
        this.hooks = unmodifiableClone(new KernelHooks(this.hooks).addHooks(hooks));
        return this;
    }

    /**
     * Supply prompt execution settings to the function invocation.
     *
     * @param promptExecutionSettings The prompt execution settings to supply to the function
     *                                invocation.
     * @return this {@code FunctionInvocation} for fluent chaining.
     */
    public FunctionInvocation<T> withPromptExecutionSettings(
        @Nullable PromptExecutionSettings promptExecutionSettings) {
        logSubscribeWarning();
        this.promptExecutionSettings = promptExecutionSettings;
        return this;
    }

    /**
     * Supply tool call behavior to the function invocation.
     *
     * @param toolCallBehavior The tool call behavior to supply to the function invocation.
     * @return this {@code FunctionInvocation} for fluent chaining.
     */
    public FunctionInvocation<T> withToolCallBehavior(@Nullable ToolCallBehavior toolCallBehavior) {
        logSubscribeWarning();
        this.toolCallBehavior = unmodifiableClone(toolCallBehavior);
        return this;
    }

    /**
     * Supply a type converter to the function invocation.
     *
     * @param typeConverter The type converter to supply to the function invocation.
     * @return this {@code FunctionInvocation} for fluent chaining.
     */
    public FunctionInvocation<T> withTypeConverter(ContextVariableTypeConverter<?> typeConverter) {
        logSubscribeWarning();
        contextVariableTypes.putConverter(typeConverter);
        return this;
    }

    /**
     * Supply a context variable type to the function invocation.
     *
     * @param contextVariableTypes The context variable types to supply to the function invocation.
     * @return this {@code FunctionInvocation} for fluent chaining.
     */
    public FunctionInvocation<T> withTypes(ContextVariableTypes contextVariableTypes) {
        logSubscribeWarning();
        this.contextVariableTypes.putConverters(contextVariableTypes);
        return this;
    }

    /**
     * Use an invocation context variable to supply the types, tool call behavior, prompt execution
     * settings, and kernel hooks to the function invocation.
     *
     * @param invocationContext The invocation context to supply to the function invocation.
     * @return this {@code FunctionInvocation} for fluent chaining.
     */
    public FunctionInvocation<T> withInvocationContext(
        @Nullable InvocationContext invocationContext) {
        if (invocationContext == null) {
            return this;
        }
        logSubscribeWarning();
        withTypes(invocationContext.getContextVariableTypes());
        withToolCallBehavior(invocationContext.getToolCallBehavior());
        withPromptExecutionSettings(invocationContext.getPromptExecutionSettings());
        addKernelHooks(invocationContext.getKernelHooks());
        return this;
    }

    private void logSubscribeWarning() {
        if (isSubscribed) {
            LOGGER.warn(
                "Attempting to modify function {}.{} after it has already been subscribed to. This is not necessarily an error but may be an unusual pattern and indicate a potential bug.",
                function.getPluginName(), function.getName());
        }
    }

    /**
     * This method hanldes the reactive stream when the KernelFunciton is invoked.
     *
     * @param coreSubscriber The subscriber to subscribe to the function invocation.
     */
    @Override
    public void subscribe(CoreSubscriber<? super FunctionResult<T>> coreSubscriber) {

        if (isSubscribed) {
            LOGGER.warn(
                "Function {}.{} has already been subscribed to. This is not necessarily an error but may be an unusual pattern.",
                function.getPluginName(), function.getName());
        }

        isSubscribed = true;

        performSubscribe(
            coreSubscriber,
            kernel,
            function,
            arguments,
            resultType,
            new InvocationContext(
                hooks,
                promptExecutionSettings,
                toolCallBehavior,
                contextVariableTypes));
    }

}
