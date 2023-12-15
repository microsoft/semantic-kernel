package com.microsoft.semantickernel.plugin;

import com.microsoft.semantickernel.ServiceProvider;
import com.microsoft.semantickernel.Todo;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.plugin.annotations.DefineKernelFunction;
import com.microsoft.semantickernel.plugin.annotations.KernelFunctionParameter;
import java.lang.reflect.Method;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.stream.Collectors;
import javax.annotation.Nullable;

public class KernelPluginFactory {

    /// <summary>Creates a plugin that wraps the specified target object.</summary>
    /// <param name="target">The instance of the class to be wrapped.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <paramref name="target"/>.
    /// </param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <remarks>
    /// Public methods decorated with <see cref="KernelFunctionAttribute"/> will be included in the plugin.
    /// Attributed methods must all have different names; overloads are not supported.
    /// </remarks>
    public static KernelPlugin createFromObject(
        Object target,
        @Nullable String pluginName) {
        List<KernelFunction> methods =
            Arrays.stream(target.getClass().getMethods())
                .filter(method -> method.isAnnotationPresent(DefineKernelFunction.class))
                .map(
                    method -> {
                        DefineKernelFunction annotation = method.getAnnotation(
                            DefineKernelFunction.class);
                        KernelReturnParameterMetadata kernelReturnParameterMetadata =
                            new KernelReturnParameterMetadata(
                                annotation.returnDescription()
                            );

                        return KernelFunctionFactory
                            .createFromMethod(
                                method,
                                target,
                                annotation.name(),
                                annotation.description(),
                                getParameters(method),
                                kernelReturnParameterMetadata);
                    })
                .collect(Collectors.toList());

        return createFromFunctions(pluginName, methods);
    }

    /// <summary>Initializes the new plugin from the provided name and function collection.</summary>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="functions">The initial functions to be available as part of the plugin.</param>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is an invalid plugin name.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="functions"/> contains a null function.</exception>
    /// <exception cref="ArgumentException"><paramref name="functions"/> contains two functions with the same name.</exception>
    public static KernelPlugin createFromFunctions(
        String pluginName,
        @Nullable List<KernelFunction> functions) {

        if (functions == null) {
            return new DefaultKernelPlugin(
                pluginName,
                null,
                new HashMap<>()
            );
        }

        return new DefaultKernelPlugin(
            pluginName,
            null,
            functions.stream().collect(Collectors.toMap(KernelFunction::getName, f -> f))
        );
    }

    /// <summary>Initializes the new plugin from the provided name, description, and function collection.</summary>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="description">A description of the plugin.</param>
    /// <param name="functions">The initial functions to be available as part of the plugin.</param>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is an invalid plugin name.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="functions"/> contains a null function.</exception>
    /// <exception cref="ArgumentException"><paramref name="functions"/> contains two functions with the same name.</exception>
    public static KernelPlugin createFromFunctions(String pluginName,
        @Nullable String description,
        @Nullable List<KernelFunction> functions) {
        throw new Todo();
    }


    private static List<KernelParameterMetadata> getParameters(Method method) {
        return Arrays.stream(method.getParameters())
            .filter(
                parameter ->
                    parameter.isAnnotationPresent(KernelFunctionParameter.class))
            .map(
                parameter -> {
                    KernelFunctionParameter annotation =
                        parameter.getAnnotation(KernelFunctionParameter.class);

                    return new KernelParameterMetadata(
                        annotation.name(),
                        annotation.description(),
                        annotation.defaultValue(),
                        annotation.required());
                })
            .collect(Collectors.toList());
    }
}
