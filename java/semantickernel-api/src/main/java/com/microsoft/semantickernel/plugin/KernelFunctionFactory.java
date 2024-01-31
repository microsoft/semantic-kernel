package com.microsoft.semantickernel.plugin;

import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromMethod;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromPrompt;
import com.microsoft.semantickernel.semanticfunctions.KernelPromptTemplateFactory;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateFactory;
import java.lang.reflect.Method;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import javax.annotation.Nullable;

public class KernelFunctionFactory {


    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a method, specified via an <see cref="MethodInfo"/> instance
    /// and an optional target object if the method is an instance method.
    /// </summary>
    /// <param name="method">The method to be represented via the created <see cref="KernelFunction"/>.</param>
    /// <param name="target">The target object for the <paramref name="method"/> if it represents an instance method. This should be null if and only if <paramref name="method"/> is a static method.</param>
    /// <param name="functionName">Optional function name. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="description">Optional description of the method. If null, it will default to one derived from the method represented by <paramref name="method"/>, if possible (e.g. via a <see cref="DescriptionAttribute"/> on the method).</param>
    /// <param name="parameters">Optional parameter descriptions. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="returnParameter">Optional return parameter description. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>The created <see cref="KernelFunction"/> wrapper for <paramref name="method"/>.</returns>
    public static KernelFunction createFromMethod(
        Method method,
        Object target,
        @Nullable String functionName,
        @Nullable String description,
        @Nullable List<KernelParameterMetadata<?>> parameters,
        @Nullable KernelReturnParameterMetadata<?> returnParameter) {
        return KernelFunctionFromMethod.create(method, target, functionName, description,
            parameters, returnParameter);
    }


    /**
     * Creates a {@link KernelFunction} instance for a prompt specified via a prompt template.
     *
     * @param promptTemplate Prompt template for the function.
     * @return The created {@link KernelFunction} for invoking the prompt.
     */
    public static KernelFunction createFromPrompt(String promptTemplate) {
        return createFromPrompt(promptTemplate, null, null, null, null, null);
    }

    /**
     * Creates a {@link KernelFunction} instance for a prompt specified via a prompt template.
     *
     * @param promptTemplate        Prompt template for the function.
     * @param executionSettings     Default execution settings to use when invoking this prompt
     *                              function.
     * @param functionName          The name to use for the function. If null, it will default to a
     *                              randomly generated name.
     * @param description           The description to use for the function.
     * @param templateFormat        The template format of {@code promptTemplate}. This must be
     *                              provided if {@code promptTemplateFactory} is not null.
     * @param promptTemplateFactory The {@link PromptTemplateFactory} to use when interpreting the
     *                              {@code promptTemplate} into a {@link PromptTemplate}. If null, a
     *                              default factory will be used.
     * @return The created {@link KernelFunction} for invoking the prompt.
     */
    public static KernelFunction createFromPrompt(
        String promptTemplate,
        @Nullable PromptExecutionSettings executionSettings,
        @Nullable String functionName,
        @Nullable String description,
        @Nullable String templateFormat,
        @Nullable PromptTemplateFactory promptTemplateFactory) {
        return KernelFunctionFromPrompt.create(
            promptTemplate,
            createSettingsDictionary(executionSettings),
            functionName,
            description,
            templateFormat,
            promptTemplateFactory);
    }

    public static KernelFunction createFromPrompt(
        PromptTemplateConfig promptConfig,
        @Nullable PromptTemplateFactory promptTemplateFactory) {

        if (promptTemplateFactory == null) {
            promptTemplateFactory = new KernelPromptTemplateFactory();
        }

        return KernelFunctionFactory.create(promptTemplateFactory.tryCreate(promptConfig),
            promptConfig);
    }

    public static KernelFunction create(
        PromptTemplate promptTemplate,
        PromptTemplateConfig promptConfig) {
        return new KernelFunctionFromPrompt(
            promptTemplate,
            promptConfig,
            null);
    }

    private static Map<String, PromptExecutionSettings> createSettingsDictionary(
        @Nullable
        PromptExecutionSettings executionSettings) {
        HashMap<String, PromptExecutionSettings> map = new HashMap<>();
        if (executionSettings != null) {
            map.put("default", executionSettings);
        }
        return map;
    }
}
