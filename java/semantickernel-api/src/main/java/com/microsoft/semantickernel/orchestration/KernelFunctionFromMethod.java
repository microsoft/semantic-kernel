package com.microsoft.semantickernel.orchestration;

import static com.microsoft.semantickernel.plugin.annotations.KernelFunctionParameter.NO_DEFAULT_VALUE;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.exceptions.AIException;
import com.microsoft.semantickernel.exceptions.AIException.ErrorCodes;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableType;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter;
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
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.function.Function;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;
import javax.annotation.Nullable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

public class KernelFunctionFromMethod extends DefaultKernelFunction {

    private final static Logger LOGGER = LoggerFactory.getLogger(KernelFunctionFromMethod.class);

    private final ImplementationFunc function;

    private KernelFunctionFromMethod(
        ImplementationFunc implementationFunc,
        String functionName,
        String description,
        List<KernelParameterMetadata> parameters,
        KernelReturnParameterMetadata returnParameter) {
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
    public <T> Flux<StreamingContent<T>> invokeStreamingAsync(
        Kernel kernel,
        @Nullable KernelArguments arguments,
        ContextVariableType<T> variableType) {
        return function
            .invoke(kernel, this, arguments)
            .map(it -> {
                return new StreamingContent<>(variableType.getConverter().fromObject(it));
            })
            .flux();
    }

    @Override
    public <T> Mono<ContextVariable<T>> invokeAsync(
        Kernel kernel,
        @Nullable KernelArguments arguments,
        ContextVariableType<T> variableType) {
        return function.invoke(kernel, this, arguments)
            .map(it -> {
                return ContextVariable.of(variableType.getConverter().fromObject(it));
            });
    }

    public interface ImplementationFunc {

        <T> Mono<T> invoke(
            Kernel kernel,
            KernelFunction function,
            @Nullable
            KernelArguments arguments);
    }


    public static KernelFunction create(
        Method method,
        Object target,
        String functionName,
        String description,
        List<KernelParameterMetadata> parameters,
        KernelReturnParameterMetadata returnParameter) {

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

        return new MethodDetails(
            functionName,
            description,
            getFunction(method, target),
            getParameters(method),
            new KernelReturnParameterMetadata(returnDescription)
        );
    }


    private static ImplementationFunc getFunction(Method method, Object instance) {

        return new ImplementationFunc() {
            @Override
            public <T> Mono<T> invoke(Kernel kernel, KernelFunction function,
                @Nullable
                KernelArguments arguments) {

                //Set<Parameter> inputArgs = determineInputArgs(method);

                try {
                    List<Object> args =
                        Arrays.stream(method.getParameters())
                            .map(getParameters(method, arguments))
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
                        /*
                        if (it instanceof KernelFunctionParameter) {
                            return it;
                        } else {
                            return context.update((String) it);
                        }

                         */
                        });

                    return r;
                } catch (Exception e) {

                    throw new RuntimeException(e);
                    //return Mono.error(e);
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

    private static Function<Parameter, Object> getParameters(
        Method method,
        @Nullable
        KernelArguments context) {
        return parameter -> {
            if (KernelArguments.class.isAssignableFrom(parameter.getType())) {
                return context;
            } else {
                return getArgumentValue(method, context, parameter);
            }
        };
    }

    private static Object getArgumentValue(
        Method method,
        @Nullable KernelArguments context,
        Parameter parameter) {
        if (context == null) {
            return context;
        }
        String variableName = getGetVariableName(parameter);

        ContextVariable<?> arg = context.get(variableName);
        if (arg == null) {
            /*
            // If this is bound to input get the input value
            if (inputArgs.contains(parameter)) {
                ContextVariable<?> input = context.get(KernelArguments.MAIN_KEY);
                if (input != null) {
                    arg = input;
                }
            }

             */

            if (arg == null) {
                KernelFunctionParameter annotation =
                    parameter.getAnnotation(KernelFunctionParameter.class);
                if (annotation != null) {
                    arg = ContextVariable.of(annotation.defaultValue());

                    if (NO_DEFAULT_VALUE.equals(arg)) {
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
        }

        if (arg == null && variableName.matches("arg\\d")) {
            LOGGER.warn(formErrorMessage(method, parameter));
        }

        if (NO_DEFAULT_VALUE.equals(arg)) {
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

        if (parameter.getType().isAssignableFrom(arg.getValue().getClass())) {
            return arg.getValue();
        }

        if (isPrimative(arg.getValue().getClass(), parameter.getType())) {
            return arg.getValue();
        }

        ContextVariableTypeConverter<?> c = arg.getType().getConverter();

        Object converted = c.toObject(arg.getValue(), parameter.getType());
        if (converted != null) {
            return converted;
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

    private static Set<Parameter> determineInputArgs(Method method) {
        // Something is bound to the input if either:
        // - it is annotated with @SKFunctionInputAttribute
        // - SKFunctionParameters annotation has a name of "input"
        // - the arg name is "input"
        // - there is only 1 string argument to the function

        // Get all parameters annotated with SKFunctionInputAttribute
        List<Parameter> annotated =
            Arrays.stream(method.getParameters())
                .filter(it -> it.isAnnotationPresent(KernelFunctionParameter.class))
                .collect(Collectors.toList());

        if (annotated.size() > 1) {
            LOGGER.warn(
                "Multiple arguments of "
                    + method.getName()
                    + " have the @SKFunctionInputAttribute annotation. This is likely an"
                    + " error.");
        }

        // Get all parameters annotated with SKFunctionParameters with a name of "input"
        List<Parameter> annotatedWithName =
            Arrays.stream(method.getParameters())
                .filter(it -> it.isAnnotationPresent(KernelFunctionParameter.class))
                .filter(it -> it.getName().equals("input"))
                .collect(Collectors.toList());

        if (annotatedWithName.size() > 1) {
            LOGGER.warn(
                "Multiple arguments of "
                    + method.getName()
                    + " have the name input. This is likely an error.");
        }

        // Get all parameters named "input", this will frequently fail as compilers strip out
        // argument names
        List<Parameter> calledInput =
            Arrays.stream(method.getParameters())
                .filter(it -> getGetVariableName(it).equals("input"))
                .collect(Collectors.toList());

        // Get parameter if there is only 1 string, and it has not been annotated with
        // SKFunctionParameters
        List<Parameter> soloString =
            Arrays.stream(method.getParameters())
                .filter(it -> it.getType().equals(String.class))
                .filter(
                    it ->
                        !(it.isAnnotationPresent(KernelFunctionParameter.class)
                            && !it.getAnnotation(KernelFunctionParameter.class)
                            .name()
                            .isEmpty()))
                .collect(Collectors.toList());
        if (soloString.size() > 1) {
            soloString.clear();
        }

        Set<Parameter> params = new HashSet<>();
        params.addAll(annotated);
        params.addAll(annotatedWithName);
        params.addAll(calledInput);
        params.addAll(soloString);

        if (params.size() > 1) {
            LOGGER.warn(
                "Multiple arguments of "
                    + method.getName()
                    + " are bound to the input variable. This is likely an error.");
        }

        return params;
    }

    private static List<KernelParameterMetadata> getParameters(Method method) {
        return
            Arrays.stream(method
                    .getParameters())
                .map(KernelFunctionFromMethod::toKernelParameterMetadata)
                .collect(Collectors.toList());
    }

    private static KernelParameterMetadata toKernelParameterMetadata(Parameter parameter) {
        KernelFunctionParameter annotation = parameter.getAnnotation(
            KernelFunctionParameter.class);

        String name = parameter.getName();
        String description = null;
        String defaultValue = null;
        boolean isRequired = true;

        if (annotation != null) {
            name = annotation.name();
            description = annotation.description();
            defaultValue = annotation.defaultValue();
            isRequired = annotation.required();
        }

        return new KernelParameterMetadata(
            name,
            description,
            defaultValue,
            isRequired
        );
    }
}
