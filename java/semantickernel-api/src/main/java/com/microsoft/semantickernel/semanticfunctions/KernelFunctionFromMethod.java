package com.microsoft.semantickernel.semanticfunctions;

import static com.microsoft.semantickernel.plugin.annotations.KernelFunctionParameter.NO_DEFAULT_VALUE;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.exceptions.AIException;
import com.microsoft.semantickernel.exceptions.AIException.ErrorCodes;
import com.microsoft.semantickernel.hooks.FunctionInvokedEvent;
import com.microsoft.semantickernel.hooks.FunctionInvokingEvent;
import com.microsoft.semantickernel.hooks.KernelHooks;
import com.microsoft.semantickernel.orchestration.DefaultKernelFunction;
import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.KernelFunctionMetadata;
import com.microsoft.semantickernel.orchestration.MethodDetails;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableType;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter.NoopConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import com.microsoft.semantickernel.plugin.KernelParameterMetadata;
import com.microsoft.semantickernel.plugin.KernelReturnParameterMetadata;
import com.microsoft.semantickernel.plugin.annotations.DefineKernelFunction;
import com.microsoft.semantickernel.plugin.annotations.KernelFunctionParameter;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Parameter;
import java.util.Arrays;
import java.util.List;
import java.util.function.Function;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;
import javax.annotation.Nullable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

public class KernelFunctionFromMethod extends DefaultKernelFunction {

    private final static Logger LOGGER = LoggerFactory.getLogger(KernelFunctionFromMethod.class);

    private final ImplementationFunc function;

    private KernelFunctionFromMethod(
        ImplementationFunc implementationFunc,
        String functionName,
        @Nullable
        String description,
        @Nullable
        List<KernelParameterMetadata<?>> parameters,
        KernelReturnParameterMetadata<?> returnParameter) {
        super(
            new KernelFunctionMetadata(
                functionName,
                description,
                parameters,
                returnParameter
            ),
            null
        );
        this.function = implementationFunc;
    }

    @Override
    public <T> Mono<FunctionResult<T>> invokeAsync(
        Kernel kernel,
        @Nullable KernelArguments arguments,
        @Nullable ContextVariableType<T> variableType) {
        return invokeAsync(
            kernel,
            arguments,
            kernel.getHookService(),
            variableType);
    }

    @Override
    public <T> Mono<FunctionResult<T>> invokeAsync(
        Kernel kernel,
        @Nullable KernelArguments arguments,
        @Nullable KernelHooks kernelHooks,
        @Nullable ContextVariableType<T> variableType) {

        if (kernelHooks == null) {
            kernelHooks = kernel.getHookService();
        }

        return function
            .invoke(kernel, this, arguments, kernelHooks)
            .map(it -> convertVariableToReturnType(variableType, it));
    }

    private <T> FunctionResult convertVariableToReturnType(
        @Nullable ContextVariableType<T> variableType,
        FunctionResult<Object> it) {
        if (variableType != null) {
            return new FunctionResult<>(
                variableType.of(it.getResult()),
                it.getMetadata());
        } else {
            Object result = it.getResult();
            if (result != null && getMetadata().getReturnParameter().getParameterType()
                .isAssignableFrom(result.getClass())) {
                return new FunctionResult<>(
                    new ContextVariable<>(
                        new ContextVariableType<>(
                            new NoopConverter(
                                getMetadata().getReturnParameter().getParameterType()),
                            getMetadata().getReturnParameter().getParameterType()
                        ),
                        it.getResult())
                );
            }
            throw new RuntimeException("Unable to convert result to type: "
                + getMetadata().getReturnParameter().getParameterType().getName());
        }
    }

    public interface ImplementationFunc {

        <T> Mono<FunctionResult<T>> invoke(
            Kernel kernel,
            KernelFunction function,
            @Nullable
            KernelArguments arguments,
            KernelHooks kernelHooks);
    }


    public static KernelFunction create(
        Method method,
        Object target,
        @Nullable
        String functionName,
        @Nullable
        String description,
        @Nullable
        List<KernelParameterMetadata<?>> parameters,
        @Nullable
        KernelReturnParameterMetadata<?> returnParameter) {

        MethodDetails methodDetails = getMethodDetails(functionName, method, target);

        if (description == null) {
            description = methodDetails.getDescription();
        }

        if (parameters == null || parameters.isEmpty()) {
            parameters = methodDetails.getParameters();
        }

        if (returnParameter == null) {
            returnParameter = methodDetails.getReturnParameter();
        }

        return new KernelFunctionFromMethod(
            methodDetails.getFunction(),
            methodDetails.getName(),
            description,
            parameters,
            returnParameter);
    }


    private static MethodDetails getMethodDetails(
        @Nullable
        String functionName,
        Method method,
        Object target) {

        DefineKernelFunction annotation = method.getAnnotation(DefineKernelFunction.class);

        String description = null;
        String returnDescription = null;
        if (annotation != null) {
            description = annotation.description();
            returnDescription = annotation.returnDescription();
        }

        if (functionName == null) {
            functionName = method.getName();
        }

        return new MethodDetails(
            functionName,
            description,
            getFunction(method, target),
            getParameters(method),
            new KernelReturnParameterMetadata<>(
                returnDescription,
                method.getReturnType()
            )
        );
    }


    private static ImplementationFunc getFunction(Method method, Object instance) {

        return new ImplementationFunc() {
            @Override
            public <T> Mono<FunctionResult<T>> invoke(
                Kernel kernel,
                KernelFunction function,
                @Nullable
                KernelArguments arguments,
                KernelHooks kernelHooks) {

                FunctionInvokingEvent updatedState = kernelHooks
                    .executeHooks(
                        new FunctionInvokingEvent(function, arguments));
                KernelArguments updatedArguments = updatedState.getArguments();

                try {
                    List<Object> args =
                        Arrays.stream(method.getParameters())
                            .map(getParameters(method, updatedArguments, kernel))
                            .collect(Collectors.toList());

                    Mono<?> mono;
                    if (method.getReturnType().isAssignableFrom(Mono.class)) {
                        mono = (Mono) method.invoke(instance, args.toArray());
                    } else {
                        mono = invokeAsyncFunction(method, instance, args);
                    }

                    Mono<T> r = mono
                        .map(it -> {
                            if (it instanceof Iterable) {
                                // Handle return from things like Mono<List<?>>
                                // from {{function 'input'}} as part of the prompt.
                                return (T) ((Iterable<?>) it).iterator().next();
                            } else {
                                return (T) it;
                            }
                        });

                    return r
                        .map(it -> {
                            return new FunctionResult(
                                new ContextVariable(
                                    new ContextVariableType(
                                        new NoopConverter(
                                            function
                                                .getMetadata()
                                                .getReturnParameter()
                                                .getParameterType()
                                        ),
                                        function
                                            .getMetadata()
                                            .getReturnParameter()
                                            .getParameterType()
                                    ),
                                    it));
                        })
                        .map(it -> {
                            FunctionInvokedEvent<T> updatedResult = kernelHooks
                                .executeHooks(
                                    new FunctionInvokedEvent<>(
                                        function,
                                        updatedArguments,
                                        it));
                            return updatedResult.getResult();
                        });
                } catch (Exception e) {
                    return Mono.error(e);
                }
            }
        };
    }

    private static Mono<Object> invokeAsyncFunction(
        Method method, Object instance, List<Object> args) {
        return Mono.defer(
            () ->
                Mono.fromCallable(
                        () -> {
                            try {
                                if (method.getReturnType().getName().equals("void")
                                    || method.getReturnType()
                                    .equals(Void.class)) {
                                    method.invoke(instance, args.toArray());
                                    return null;
                                } else {
                                    return method.invoke(instance, args.toArray());
                                }
                            } catch (InvocationTargetException e) {
                                throw new AIException(
                                    ErrorCodes.INVALID_REQUEST,
                                    "Function threw an exception: "
                                        + method.getName(),
                                    e.getCause());
                            } catch (IllegalAccessException e) {
                                throw new AIException(
                                    ErrorCodes.INVALID_REQUEST,
                                    "Unable to access function "
                                        + method.getName(),
                                    e);
                            }
                        })
                    .subscribeOn(Schedulers.boundedElastic()));
    }

    @Nullable
    private static Function<Parameter, Object> getParameters(
        Method method,
        @Nullable
        KernelArguments context,
        Kernel kernel) {
        return parameter -> {
            if (KernelArguments.class.isAssignableFrom(parameter.getType())) {
                return context;
            } else {
                return getArgumentValue(method, context, parameter, kernel);
            }
        };
    }

    @Nullable
    private static Object getArgumentValue(
        Method method,
        @Nullable KernelArguments context,
        Parameter parameter,
        Kernel kernel) {
        String variableName = getGetVariableName(parameter);

        ContextVariable<?> arg = context == null ? null : context.get(variableName);
        if (arg == null) {
            KernelFunctionParameter annotation =
                parameter.getAnnotation(KernelFunctionParameter.class);
            if (annotation != null) {
                // Convert from the defaultValue, which is a String to the argument type
                // Expectation here is that the fromPromptString method will be able to handle a null or empty string
                Class<?> type = annotation.type();
                ContextVariableType<?> cvType = ContextVariableTypes.getDefaultVariableTypeForClass(
                    type);
                if (cvType != null) {
                    String defaultValue = annotation.defaultValue();
                    Object value = cvType.getConverter().fromPromptString(defaultValue);
                    arg = ContextVariable.untypedOf(value, cvType.getConverter());
                }

                if (arg != null && NO_DEFAULT_VALUE.equals(arg.getValue())) {
                    if (!annotation.required()) {
                        return null;
                    }

                    throw new AIException(
                        AIException.ErrorCodes.INVALID_CONFIGURATION,
                        "Attempted to invoke function "
                            + method.getDeclaringClass().getName()
                            + "."
                            + method.getName()
                            + ". The context variable \""
                            + variableName
                            + "\" has not been set, and no default value is"
                            + " specified.");
                }
            }
        }

        if (arg == null && variableName.matches("arg\\d")) {
            LOGGER.warn(formErrorMessage(method, parameter));
        }

        if (arg != null && NO_DEFAULT_VALUE.equals(arg.getValue())) {
            if (parameter.getName().matches("arg\\d")) {
                throw new AIException(
                    AIException.ErrorCodes.INVALID_CONFIGURATION,
                    formErrorMessage(method, parameter));
            } else {
                throw new AIException(
                    AIException.ErrorCodes.INVALID_CONFIGURATION,
                    "Unknown arg " + parameter.getName());
            }
        }

        if (Kernel.class.isAssignableFrom(parameter.getType())) {
            return kernel;
        }

        KernelFunctionParameter annotation = parameter.getAnnotation(KernelFunctionParameter.class);
        if (annotation == null || annotation.type() == null) {
            return arg;
        }

        Class<?> type = annotation.type();

        if (!parameter.getType().isAssignableFrom(type)) {
            throw new AIException(
                AIException.ErrorCodes.INVALID_CONFIGURATION,
                "Annotation on method: " + method.getName() + " requested conversion to type: "
                    + type.getName() + ", however this cannot be assigned to parameter of type: "
                    + parameter.getType());
        }

        Object value = arg;

        if (arg != null) {

            if (parameter.getType().isAssignableFrom(arg.getType().getClazz())) {
                return arg.getValue();
            }

            if (isPrimative(arg.getType().getClazz(), parameter.getType())) {
                return arg.getValue();
            }

            ContextVariableTypeConverter<?> c = arg.getType().getConverter();

            Object converted = c.toObject(arg.getValue(), parameter.getType());
            if (converted != null) {
                return converted;
            }
        }

        // Well-known types only
        ContextVariableType<?> converter = ContextVariableTypes.getDefaultVariableTypeForClass(
            type);
        if (converter != null) {
            try {
                value = converter.getConverter().fromObject(arg);
            } catch (NumberFormatException nfe) {
                throw new AIException(
                    AIException.ErrorCodes.INVALID_CONFIGURATION,
                    "Invalid value for "
                        + parameter.getName()
                        + " expected "
                        + type.getSimpleName()
                        + " but got "
                        + arg);
            }
        }
        return value;
    }

    @SuppressWarnings("OperatorPrecedence")
    private static boolean isPrimative(Class<?> argType, Class<?> param) {
        return (argType == Byte.class || argType == byte.class) && (param == Byte.class
            || param == byte.class) ||
            (argType == Integer.class || argType == int.class) && (param == Integer.class
                || param == int.class) ||
            (argType == Long.class || argType == long.class) && (param == Long.class
                || param == long.class) ||
            (argType == Double.class || argType == double.class) && (param == Double.class
                || param == double.class) ||
            (argType == Float.class || argType == float.class) && (param == Float.class
                || param == float.class) ||
            (argType == Short.class || argType == short.class) && (param == Short.class
                || param == short.class) ||
            (argType == Boolean.class || argType == boolean.class) && (param == Boolean.class
                || param == boolean.class) ||
            (argType == Character.class || argType == char.class) && (param == Character.class
                || param == char.class);
    }

    private static String getGetVariableName(Parameter parameter) {
        KernelFunctionParameter annotation = parameter.getAnnotation(KernelFunctionParameter.class);

        if (annotation == null || annotation.name() == null || annotation.name().isEmpty()) {
            return parameter.getName();
        }
        return annotation.name();
    }


    private static String formErrorMessage(Method method, Parameter parameter) {
        Matcher matcher = Pattern.compile("arg(\\d)").matcher(parameter.getName());
        matcher.find();
        return "For the function "
            + method.getDeclaringClass().getName()
            + "."
            + method.getName()
            + ", the unknown parameter"
            + " name was detected as \""
            + parameter.getName()
            + "\" this is argument"
            + " number "
            + matcher.group(1)
            + " to the function, this indicates that the argument name for this function was"
            + " removed during compilation and semantic-kernel is unable to determine the name"
            + " of the parameter. To support this function the argument must be annotated with"
            + " @SKFunctionParameters or @SKFunctionInputAttribute. Alternatively the function"
            + " was invoked with a required context variable missing and no default value.";
    }

    private static List<KernelParameterMetadata<?>> getParameters(Method method) {
        return
            Arrays.stream(method
                    .getParameters())
                .map(KernelFunctionFromMethod::toKernelParameterMetadata)
                .collect(Collectors.toList());
    }

    private static KernelParameterMetadata<?> toKernelParameterMetadata(Parameter parameter) {
        KernelFunctionParameter annotation = parameter.getAnnotation(
            KernelFunctionParameter.class);

        String name = parameter.getName();
        String description = null;
        String defaultValue = null;
        boolean isRequired = true;
        Class<?> type = parameter.getType();

        if (annotation != null) {
            name = annotation.name();
            description = annotation.description();
            defaultValue = annotation.defaultValue();
            isRequired = annotation.required();
            type = annotation.type();
        }

        return new KernelParameterMetadata<>(
            name,
            description,
            type,
            defaultValue,
            isRequired
        );
    }
}
