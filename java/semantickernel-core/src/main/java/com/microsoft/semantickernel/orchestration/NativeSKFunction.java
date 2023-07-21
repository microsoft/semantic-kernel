// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import static com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters.NO_DEFAULT_VALUE;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.ai.AIException;
import com.microsoft.semantickernel.skilldefinition.FunctionView;
import com.microsoft.semantickernel.skilldefinition.KernelSkillsSupplier;
import com.microsoft.semantickernel.skilldefinition.ParameterView;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;
import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionInputAttribute;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Parameter;
import java.util.*;
import java.util.function.Function;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

import javax.annotation.Nullable;

/// <summary>
/// Standard Semantic Kernel callable function.
/// SKFunction is used to extend one C# <see cref="Delegate"/>, <see cref="Func{T, TResult}"/>, <see
// cref="Action"/>,
/// with additional methods required by the kernel.
/// </summary>
public class NativeSKFunction extends AbstractSkFunction<Void> {

    private static final Logger LOGGER = LoggerFactory.getLogger(NativeSKFunction.class);

    private final SKNativeTask<SKContext> function;

    public NativeSKFunction(
            SKNativeTask<SKContext> delegateFunction,
            List<ParameterView> parameters,
            String skillName,
            String functionName,
            String description,
            KernelSkillsSupplier skillCollection) {
        super(parameters, skillName, functionName, description, skillCollection);
        // TODO
        // Verify.NotNull(delegateFunction, "The function delegate is empty");
        // Verify.ValidSkillName(skillName);
        // Verify.ValidFunctionName(functionName);
        // Verify.ParametersUniqueness(parameters);

        this.function = delegateFunction;
    }

    @Override
    public FunctionView describe() {
        return new FunctionView(
                super.getName(),
                super.getSkillName(),
                super.getDescription(),
                super.getParametersView(),
                false,
                false);
    }

    @Override
    public Class<Void> getType() {
        return Void.class;
    }

    @Override
    public void registerOnKernel(Kernel kernel) {
        // No actions needed
    }

    private static class MethodDetails {
        public final boolean hasSkFunctionAttribute;
        public final SKNativeTask<SKContext> function;
        public final List<ParameterView> parameters;
        public final String name;
        public final String description;

        private MethodDetails(
                boolean hasSkFunctionAttribute,
                SKNativeTask<SKContext> function,
                List<ParameterView> parameters,
                String name,
                String description) {
            this.hasSkFunctionAttribute = hasSkFunctionAttribute;
            this.function = function;
            this.parameters = parameters;
            this.name = name;
            this.description = description;
        }
    }

    public static NativeSKFunction fromNativeMethod(
            Method methodSignature,
            Object methodContainerInstance,
            String skillName,
            KernelSkillsSupplier kernelSkillsSupplier) {
        if (skillName == null || skillName.isEmpty()) {
            skillName = ReadOnlySkillCollection.GlobalSkill;
        }

        MethodDetails methodDetails = getMethodDetails(methodSignature, methodContainerInstance);

        // If the given method is not a valid SK function
        if (!methodSignature.isAnnotationPresent(DefineSKFunction.class)) {
            throw new RuntimeException("Not a valid function");
        }

        return new NativeSKFunction(
                methodDetails.function,
                methodDetails.parameters,
                skillName,
                methodDetails.name,
                methodDetails.description,
                kernelSkillsSupplier);
    }

    // Run the native function
    @Override
    protected Mono<SKContext> invokeAsyncInternal(SKContext context, @Nullable Void settings) {
        return this.function.run(context);
    }

    private static MethodDetails getMethodDetails(
            Method methodSignature, Object methodContainerInstance) {
        // Verify.NotNull(methodSignature, "Method is NULL");

        // String name = methodSignature.getName();

        boolean hasSkFunctionAttribute =
                methodSignature.isAnnotationPresent(DefineSKFunction.class);

        if (!hasSkFunctionAttribute) {
            throw new RuntimeException("method is not annotated with DefineSKFunction");
        }
        SKNativeTask<SKContext> function = getFunction(methodSignature, methodContainerInstance);

        // boolean hasStringParam =
        //    Arrays.asList(methodSignature.getGenericParameterTypes()).contains(String.class);

        String name = methodSignature.getAnnotation(DefineSKFunction.class).name();

        if (name == null || name.isEmpty()) {
            name = methodSignature.getName();
        }

        String description = methodSignature.getAnnotation(DefineSKFunction.class).description();

        List<ParameterView> parameters = getParameters(methodSignature);

        return new MethodDetails(hasSkFunctionAttribute, function, parameters, name, description);
    }

    private static List<ParameterView> getParameters(Method method) {

        List<ParameterView> params =
                Arrays.stream(method.getParameters())
                        .filter(
                                parameter ->
                                        parameter.isAnnotationPresent(SKFunctionParameters.class)
                                                || parameter.isAnnotationPresent(
                                                        SKFunctionInputAttribute.class))
                        .map(
                                parameter -> {
                                    if (parameter.isAnnotationPresent(SKFunctionParameters.class)) {
                                        SKFunctionParameters annotation =
                                                parameter.getAnnotation(SKFunctionParameters.class);
                                        return new ParameterView(
                                                annotation.name(),
                                                annotation.description(),
                                                annotation.defaultValue());
                                    } else {
                                        return new ParameterView("input");
                                    }
                                })
                        .collect(Collectors.toList());

        HashSet<ParameterView> out = new HashSet<>(params);

        boolean hasInput = params.stream().anyMatch(p -> p.getName().equals("input"));

        if (!hasInput) {
            List<ParameterView> inputArgs =
                    determineInputArgs(method).stream()
                            .map(
                                    parameter -> {
                                        return new ParameterView("input");
                                    })
                            .collect(Collectors.toList());
            out.addAll(inputArgs);
        }

        return new ArrayList<>(out);
    }

    private static SKNativeTask<SKContext> getFunction(Method method, Object instance) {
        return (contextInput) -> {
            SKContext context = contextInput.copy();

            Set<Parameter> inputArgs = determineInputArgs(method);

            try {
                List<Object> args =
                        Arrays.stream(method.getParameters())
                                .map(getParameters(method, context, inputArgs))
                                .collect(Collectors.toList());

                Mono mono;
                if (method.getReturnType().isAssignableFrom(Mono.class)) {
                    try {
                        mono = (Mono) method.invoke(instance, args.toArray());
                    } catch (IllegalAccessException | InvocationTargetException e) {
                        return Mono.error(e);
                    }
                } else {
                    mono = invokeAsyncFunction(method, instance, args);
                }

                return mono.map(
                        it -> {
                            if (it instanceof SKContext) {
                                return it;
                            } else {
                                return context.update((String) it);
                            }
                        });
            } catch (Exception e) {
                return Mono.error(e);
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
                                                Object result =
                                                        method.invoke(instance, args.toArray());

                                                return result;
                                            } catch (IllegalAccessException
                                                    | InvocationTargetException e) {
                                                throw new RuntimeException(e.getCause());
                                            }
                                        })
                                .subscribeOn(Schedulers.boundedElastic()));
    }

    private static Function<Parameter, Object> getParameters(
            Method method, SKContext context, Set<Parameter> inputArgs) {
        return parameter -> {
            if (SKContext.class.isAssignableFrom(parameter.getType())) {
                return context;
            } else {
                return getArgumentValue(method, context, parameter, inputArgs);
            }
        };
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

    private static String getArgumentValue(
            Method method, SKContext context, Parameter parameter, Set<Parameter> inputArgs) {
        String variableName = getGetVariableName(parameter);

        String arg = context.getVariables().get(variableName);
        if (arg == null) {
            // If this is bound to input get the input value
            if (inputArgs.contains(parameter)) {
                String input = context.getVariables().get(ContextVariables.MAIN_KEY);
                if (input != null) {
                    arg = input;
                }
            }

            if (arg == null) {
                SKFunctionParameters annotation =
                        parameter.getAnnotation(SKFunctionParameters.class);
                if (annotation != null) {
                    arg = annotation.defaultValue();

                    if (NO_DEFAULT_VALUE.equals(arg)) {
                        if (!annotation.required()) {
                            return null;
                        }

                        throw new AIException(
                                AIException.ErrorCodes.InvalidConfiguration,
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
                        AIException.ErrorCodes.InvalidConfiguration,
                        formErrorMessage(method, parameter));
            } else {
                throw new AIException(
                        AIException.ErrorCodes.InvalidConfiguration,
                        "Unknown arg " + parameter.getName());
            }
        }
        return arg;
    }

    private static String getGetVariableName(Parameter parameter) {
        SKFunctionParameters annotation = parameter.getAnnotation(SKFunctionParameters.class);

        if (annotation == null || annotation.name() == null || annotation.name().isEmpty()) {
            return parameter.getName();
        }
        return annotation.name();
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
                        .filter(it -> it.isAnnotationPresent(SKFunctionInputAttribute.class))
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
                        .filter(it -> it.isAnnotationPresent(SKFunctionParameters.class))
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
                                        !(it.isAnnotationPresent(SKFunctionParameters.class)
                                                && !it.getAnnotation(SKFunctionParameters.class)
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
}
