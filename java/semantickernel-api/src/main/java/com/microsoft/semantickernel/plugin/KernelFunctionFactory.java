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

/**
 * Factory for creating {@link KernelFunction} instances.
 */
public class KernelFunctionFactory {

    /**
     * Creates a {@link KernelFunction} instance for a method, specified via a {@link Method} instance
     * @param <T> The return type of the method.
     * @param method The method to be represented via the created {@link KernelFunction}.
     * @param target The target object for the {@code method} if it represents an instance method. This should be null if and only if {@code method} is a static method.
     * @param functionName Optional function name. If null, it will default to one derived from the method represented by {@code method}.
     * @param description Optional description of the method. If null, it will default to one derived from the method represented by {@code method}, if possible (e.g. via a {@link DescriptionAttribute} on the method).
     * @param parameters Optional parameter descriptions. If null, it will default to one derived from the method represented by {@code method}.
     * @param returnParameter Optional return parameter description. If null, it will default to one derived from the method represented by {@code method}.
     * @return The created {@link KernelFunction} wrapper for {@code method}.
     */
    public static <T> KernelFunction<T> createFromMethod(
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
    public static <T> KernelFunction<T> createFromPrompt(String promptTemplate) {
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
    public static <T> KernelFunction<T> createFromPrompt(
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

    /**
     * Creates a {@link KernelFunction} instance for a prompt specified via a {@link PromptTemplateConfig}.
     *
     * @param promptConfig        A prompt template configuration for the function.
     * @param promptTemplateFactory The {@code PromptTemplateFactory} to use when interpreting
     *                               the prompt template configuration into a {@link PromptTemplate}.
     *                               If null, a default factory will be used.
     * @return The created {@link KernelFunction} for invoking the prompt.
     */
    public static <T> KernelFunction<T> createFromPrompt(
        PromptTemplateConfig promptConfig,
        @Nullable PromptTemplateFactory promptTemplateFactory) {

        if (promptTemplateFactory == null) {
            promptTemplateFactory = new KernelPromptTemplateFactory();
        }

        return KernelFunctionFactory.create(promptTemplateFactory.tryCreate(promptConfig),
            promptConfig);
    }

    /**
     * Creates a {@link KernelFunction} instance for a prompt specified via a {@link PromptTemplateConfig}.
     *
     * @param promptConfig        A prompt template configuration for the function.
     * @param promptTemplate The prompt template to use when creating the function.
     * @return The created {@link KernelFunction} for invoking the prompt.
     */
    public static <T> KernelFunction<T> create(
        PromptTemplate promptTemplate,
        PromptTemplateConfig promptConfig) {
        return new KernelFunctionFromPrompt<>(
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
