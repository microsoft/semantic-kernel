package com.microsoft.semantickernel.orchestration;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromPrompt;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateFactory;
import com.microsoft.semantickernel.templateengine.handlebars.HandlebarsPromptTemplate;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Path;
import javax.annotation.Nullable;

public class KernelFunctionYaml {

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a prompt function using the specified markdown text.
    /// </summary>
    /// <param name="text">YAML representation of the <see cref="PromptTemplateConfig"/> to use to create the prompt function</param>
    /// <param name="promptTemplateFactory">>Prompt template factory.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>The created <see cref="KernelFunction"/>.</returns>
    public static KernelFunction fromPromptYaml(
        String yaml,
        @Nullable PromptTemplateFactory promptTemplateFactory
    ) throws IOException {
        InputStream targetStream = new ByteArrayInputStream(yaml.getBytes());
        return fromYaml(targetStream, promptTemplateFactory);
    }

    public static KernelFunction fromPromptYaml(
        String yaml
    ) throws IOException {
        InputStream targetStream = new ByteArrayInputStream(yaml.getBytes());
        return fromYaml(targetStream, null);
    }

    public static KernelFunction fromYaml(Path filePath) throws IOException {
        InputStream inputStream = Thread.currentThread().getContextClassLoader()
            .getResourceAsStream(filePath.toString());
        return fromYaml(inputStream, null);
    }

    private static KernelFunction fromYaml(
        InputStream inputStream,
        @Nullable PromptTemplateFactory promptTemplateFactory
    ) throws IOException {
        ObjectMapper mapper = new ObjectMapper(new YAMLFactory());
        PromptTemplateConfig functionModel = mapper.readValue(inputStream,
            PromptTemplateConfig.class);

        PromptTemplate promptTemplate;
        if (promptTemplateFactory == null) {
            promptTemplate = new HandlebarsPromptTemplate(functionModel);
        } else {
            promptTemplate = promptTemplateFactory.tryCreate(functionModel);
        }

        return new KernelFunctionFromPrompt.Builder()
            .withName(functionModel.getName())
            .withInputParameters(functionModel.getInputVariables())
            .withPromptTemplate(promptTemplate)
            .withPluginName(functionModel.getName()) // TODO: 1.0 add plugin name
            .withExecutionSettings(functionModel.getExecutionSettings())
            .withDescription(functionModel.getDescription())
            .withOutputVariable(functionModel.getOutputVariable())
            .build();
    }

}
