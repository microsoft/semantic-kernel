package com.microsoft.semantickernel.plugin;

import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.KernelFunction.FromPromptBuilder;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromMethod;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromPrompt;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import java.lang.reflect.Method;

/**
 * Factory for creating {@link KernelFunction} instances.
 */
public class KernelFunctionFactory {

    /**
     * Creates a {@link KernelFunction} instance for a method, specified via a {@link Method}
     * instance
     *
     * @param <T>    The return type of the method.
     * @param method The method to be represented via the created {@link KernelFunction}.
     * @param target The target object for the {@code method} if it represents an instance method.
     *               This should be {@code null} if and only if {@code method} is a static method.
     * @return The created {@link KernelFunction} wrapper for {@code method}.
     */

    public static <T> KernelFunctionFromMethod.Builder<T> createFromMethod(
        Method method,
        Object target) {
        return KernelFunctionFromMethod.<T>builder()
            .withMethod(method)
            .withTarget(target);
    }

    /**
     * Creates a {@link KernelFunction} instance based on a given prompt
     *
     * @param prompt The prompt to be used for the created {@link KernelFunction}.
     * @param <T>    The return type of the method
     * @return The builder for creating a {@link KernelFunction} instance.
     */
    public static <T> FromPromptBuilder<T> createFromPrompt(String prompt) {
        return KernelFunctionFromPrompt.<T>builder()
            .withTemplate(prompt);
    }


    /**
     * Builder for creating a {@link KernelFunction} instance for a given
     * {@link PromptTemplateConfig}.
     *
     * @param promptTemplateConfiguration The configuration for the prompt template.
     * @param <T>                         The return type of the method
     * @return The builder for creating a {@link KernelFunction} instance.
     */
    public static <T> FromPromptBuilder<T> createFromPrompt(
        PromptTemplateConfig promptTemplateConfiguration) {
        return KernelFunctionFromPrompt.<T>builder()
            .withPromptTemplateConfig(promptTemplateConfiguration);
    }
}
