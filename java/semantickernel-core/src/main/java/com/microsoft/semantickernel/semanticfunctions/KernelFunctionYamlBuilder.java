package com.microsoft.semantickernel.semanticfunctions;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.KernelFunctionYaml;
import com.microsoft.semantickernel.templateengine.handlebars.HandlebarsPromptTemplate;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Path;
import javax.annotation.Nullable;

public class KernelFunctionYamlBuilder implements KernelFunctionYaml.Builder {

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a prompt function using the specified markdown text.
    /// </summary>
    /// <param name="text">YAML representation of the <see cref="PromptTemplateConfig"/> to use to create the prompt function</param>
    /// <param name="promptTemplateFactory">>Prompt template factory.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>The created <see cref="KernelFunction"/>.</returns>
    public KernelFunction fromPromptYaml(
        String yaml,
        @Nullable PromptTemplateFactory promptTemplateFactory
    ) throws IOException {
        ObjectMapper mapper = new ObjectMapper(new YAMLFactory());

        PromptTemplateConfig functionModel = mapper.readValue(yaml, PromptTemplateConfig.class);

        return new KernelFunctionFromPrompt.Builder()
            .build(functionModel);
    }

    public KernelFunction fromPromptYaml(
        String text
    ) throws IOException {
        return fromPromptYaml(text, null);
    }

    public KernelFunction fromYaml(Path filePath) throws IOException {
        return fromYaml(filePath.toAbsolutePath().toString());
    }

    public KernelFunction fromYaml(String filePath) throws IOException {
        ObjectMapper mapper = new ObjectMapper(new YAMLFactory());
        InputStream inputStream =
            Thread.currentThread().getContextClassLoader().getResourceAsStream(filePath);

        PromptTemplateConfig functionModel = mapper.readValue(inputStream,
            PromptTemplateConfig.class);

        return new KernelFunctionFromPrompt.Builder()
            .withName(functionModel.getName())
            .withInputParameters(functionModel.getInputVariables())
            .withPromptTemplate(new HandlebarsPromptTemplate(functionModel))
            .withPluginName(functionModel.getName()) // TODO: 1.0 add plugin name
            .withExecutionSettings(functionModel.getExecutionSettings())
            .withDescription(functionModel.getDescription())
            .build();
    }
}
