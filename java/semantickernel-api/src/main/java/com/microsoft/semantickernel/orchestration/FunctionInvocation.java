package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.exceptions.SKException;
import com.microsoft.semantickernel.hooks.KernelHook;
import com.microsoft.semantickernel.hooks.KernelHooks;
import com.microsoft.semantickernel.hooks.KernelHooks.UnmodifiableKernelHooks;
import com.microsoft.semantickernel.orchestration.ToolCallBehavior.UnmodifiableToolCallBehavior;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableType;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes;
import java.util.function.BiConsumer;
import javax.annotation.Nullable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import reactor.core.CoreSubscriber;
import reactor.core.publisher.Mono;
import reactor.core.publisher.SynchronousSink;

public class FunctionInvocation<T> extends Mono<FunctionResult<T>> {

    private static final Logger LOGGER = LoggerFactory.getLogger(FunctionInvocation.class);

    protected final KernelFunction<?> function;

    protected final Kernel kernel;
    @Nullable
    protected final ContextVariableType<T> resultType;

    @Nullable
    protected KernelFunctionArguments arguments;
    @Nullable
    protected UnmodifiableKernelHooks hooks;
    @Nullable
    protected PromptExecutionSettings promptExecutionSettings;
    @Nullable
    protected UnmodifiableToolCallBehavior toolCallBehavior;
    protected final ContextVariableTypes contextVariableTypes = new ContextVariableTypes();


    public FunctionInvocation(
        Kernel kernel,
        KernelFunction<T> function) {
        this.function = function;
        this.kernel = kernel;
        this.resultType = null;
        this.addKernelHooks(kernel.getGlobalKernelHooks());
    }

    public FunctionInvocation(
        Kernel kernel,
        KernelFunction<?> function,
        @Nullable
        ContextVariableType<T> resultType) {
        this.function = function;
        this.kernel = kernel;
        this.resultType = resultType;
        if (resultType != null) {
            contextVariableTypes.putConverter(resultType.getConverter());
        }
        this.addKernelHooks(kernel.getGlobalKernelHooks());
    }

    public FunctionInvocation<T> withArguments(
        @Nullable
        KernelFunctionArguments arguments) {
        if (arguments == null) {
            this.arguments = null;
        } else {
            this.arguments = new KernelFunctionArguments(arguments);
        }
        return this;
    }

    public <U> FunctionInvocation<U> withResultType(ContextVariableType<U> resultType) {
        return new FunctionInvocation<>(
            kernel,
            function,
            resultType)
            .withArguments(arguments)
            .addKernelHooks(hooks)
            .withPromptExecutionSettings(promptExecutionSettings)
            .withToolCallBehavior(toolCallBehavior);
    }

    public FunctionInvocation<T> addKernelHook(@Nullable KernelHook hook) {
        KernelHooks clone = new KernelHooks(this.hooks);
        clone.addHook(hook);
        this.hooks = unmodifiableClone(clone);
        return this;
    }

    public FunctionInvocation<T> addKernelHooks(
        @Nullable
        KernelHooks hooks) {
        if (hooks == null) {
            return this;
        }
        this.hooks = unmodifiableClone(new KernelHooks(this.hooks).addHooks(hooks));
        return this;
    }

    public FunctionInvocation<T> withPromptExecutionSettings(
        @Nullable
        PromptExecutionSettings promptExecutionSettings) {
        this.promptExecutionSettings = promptExecutionSettings;
        return this;
    }

    public FunctionInvocation<T> withToolCallBehavior(@Nullable ToolCallBehavior toolCallBehavior) {
        this.toolCallBehavior = unmodifiableClone(toolCallBehavior);
        return this;
    }

    public FunctionInvocation<T> withTypeConverter(ContextVariableType<?> typeConverter) {
        contextVariableTypes.putConverter(typeConverter.getConverter());
        return this;
    }


    public FunctionInvocation<T> withTypes(ContextVariableTypes contextVariableTypes) {
        this.contextVariableTypes.putConverters(contextVariableTypes);
        return this;
    }

    public FunctionInvocation<T> withInvocationContext(
        @Nullable InvocationContext invocationContext) {
        if (invocationContext == null) {
            return this;
        }
        withTypes(invocationContext.getContextVariableTypes());
        withToolCallBehavior(invocationContext.getToolCallBehavior());
        withPromptExecutionSettings(invocationContext.getPromptExecutionSettings());
        addKernelHooks(invocationContext.getKernelHooks());
        return this;
    }


    @Override
    public void subscribe(CoreSubscriber<? super FunctionResult<T>> coreSubscriber) {
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
                contextVariableTypes
            ));
    }

    // Extracted to static to ensure mutable state is not used
    private static <T> void performSubscribe(
        CoreSubscriber<? super FunctionResult<T>> coreSubscriber,
        Kernel kernel,
        KernelFunction<?> function,
        @Nullable
        KernelFunctionArguments arguments,
        @Nullable
        ContextVariableType<T> variableType,
        @Nullable
        InvocationContext context
    ) {
        if (variableType == null) {
            LOGGER.debug(
                "No variable type explicitly specified by calling 'withResultType' for function invocation: "
                    + function.getSkillName() + "." + function.getName() + "."
                    + " This may cause a runtime error (probably a ClassCastException) if the result type is not compatible with the expected type.");
        }

        function
            .invokeAsync(
                kernel,
                new KernelFunctionArguments(arguments),
                null,
                new InvocationContext(context))
            .handle(convertToType(variableType))
            .subscribe(coreSubscriber);
    }

    private static <T> BiConsumer<FunctionResult<?>, SynchronousSink<FunctionResult<T>>> convertToType(
        @Nullable
        ContextVariableType<T> variableType) {
        return (result, sink) -> {
            // If a specific result type was requested, convert the result to that type.
            if (variableType != null) {
                try {
                    sink.next(new FunctionResult<>(
                        ContextVariable.convert(result.getResult(), variableType),
                        result.getMetadata()
                    ));
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
        @Nullable
        ToolCallBehavior toolCallBehavior) {
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

}
