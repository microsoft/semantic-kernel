// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import javax.annotation.Nullable;

/**
 * A class for creating a {@link KernelFunction} instance from a YAML representation of a prompt
 * function.
 */
public class KernelFunctionYaml {

    /**
     * Create a KernelFunction instance for a prompt function using the specified markdown text.
     *
     * @param yaml                  YAML representation of the PromptTemplateConfig to use to create
     *                              the prompt function
     * @param promptTemplateFactory Prompt template factory.
     * @param <T>                   The return type of the function.
     * @return The created KernelFunction.
     * @throws IOException If an error occurs while reading the YAML.
     */
    public static <T> KernelFunction<T> fromPromptYaml(
        String yaml,
        @Nullable PromptTemplateFactory promptTemplateFactory) throws IOException {
        try (InputStream targetStream = new ByteArrayInputStream(
            yaml.getBytes(StandardCharsets.UTF_8))) {
            return fromYaml(targetStream, promptTemplateFactory);
        }
    }

    /**
     * Create a KernelFunction instance for a prompt function using the specified markdown text.
     *
     * @param yaml YAML representation of the PromptTemplateConfig to use to create the prompt
     *             function
     * @param <T>  The return type of the function.
     * @return The created KernelFunction.
     * @throws IOException If an error occurs while reading the YAML.
     */
    public static <T> KernelFunction<T> fromPromptYaml(
        String yaml) throws IOException {
        return fromPromptYaml(yaml, null);
    }

    /**
     * Create a KernelFunction instance for a prompt function using the specified markdown text.
     *
     * @param filePath Path to the YAML representation of the PromptTemplateConfig to use to create
     *                 the prompt function
     * @param <T>      The return type of the function.
     * @return The created KernelFunction.
     * @throws IOException If an error occurs while reading the YAML.
     */
    public static <T> KernelFunction<T> fromYaml(Path filePath) throws IOException {
        ClassLoader classLoader = Thread.currentThread().getContextClassLoader();
        try (InputStream inputStream = classLoader.getResourceAsStream(filePath.toString())) {
            return fromYaml(inputStream, null);
        }
    }

    @SuppressWarnings({ "unchecked", "rawtypes" })
    private static <T> KernelFunction<T> fromYaml(
        InputStream inputStream,
        @Nullable PromptTemplateFactory promptTemplateFactory) throws IOException {
        ObjectMapper mapper = new ObjectMapper(new YAMLFactory());
        PromptTemplateConfig functionModel = mapper.readValue(inputStream,
            PromptTemplateConfig.class);

        PromptTemplate promptTemplate;
        if (promptTemplateFactory == null) {
            promptTemplate = PromptTemplateFactory.build(functionModel);
        } else {
            promptTemplate = promptTemplateFactory.tryCreate(functionModel);
        }

        return (KernelFunction<T>) new KernelFunctionFromPrompt.Builder()
            .withName(functionModel.getName())
            .withInputParameters(functionModel.getInputVariables())
            .withPromptTemplate(promptTemplate)
            .withExecutionSettings(functionModel.getExecutionSettings())
            .withDescription(functionModel.getDescription())
            .withOutputVariable(functionModel.getOutputVariable())
            .build();
    }

}
