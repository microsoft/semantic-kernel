// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

import static org.junit.jupiter.api.Assertions.assertEquals;

import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import org.junit.jupiter.api.Test;

@SuppressWarnings("DoubleBraceInitialization")
public class PromptTemplateConfigTest {

    @Test
    void testInstanceMadeWithBuilderEqualsInstanceMadeWithConstructor() {
        String name = "a name";
        String description = "a description";
        String template = "A template for testing {{plugin.function input}}";
        List<KernelInputVariable> kernelInputVariables = Arrays.asList(
            new KernelInputVariable("input", "java.lang.String", "a description", "default value",
                true));
        KernelOutputVariable kernelOutputVariable = new KernelOutputVariable("java.lang.String",
            "a description");

        PromptTemplateConfig expected = new PromptTemplateConfig(
            PromptTemplateConfig.CURRENT_SCHEMA,
            name,
            template,
            "semantic-kernel",
            description,
            kernelInputVariables,
            kernelOutputVariable,
            new HashMap<String, PromptExecutionSettings>() {
                {
                    put("default", PromptExecutionSettings.builder().build());
                }
            });

        PromptTemplateConfig result = PromptTemplateConfig.builder()
            .withName(name)
            .withDescription(description)
            .withTemplate(template)
            .withInputVariables(kernelInputVariables)
            .withOutputVariable(kernelOutputVariable)
            .withExecutionSettings(new HashMap<String, PromptExecutionSettings>() {
                {
                    put("default", PromptExecutionSettings.builder().build());
                }
            })
            .build();

        assertEquals(expected, result);
    }

    @Test
    void testDefaultTemplateBuilder() {
        String name = "a name";
        String description = "a description";
        String template = "A template for testing {{plugin.function input}}";
        String templateFormat = "semantic-kernel";
        List<KernelInputVariable> kernelInputVariables = Arrays.asList(
            new KernelInputVariable("input", "java.lang.String", "a description", "default value",
                true));
        KernelOutputVariable kernelOutputVariable = new KernelOutputVariable("java.lang.String",
            "a description");
        HashMap<String, PromptExecutionSettings> executionSettings = new HashMap<String, PromptExecutionSettings>() {
            {
                put("default", PromptExecutionSettings.builder().build());
            }
        };

        PromptTemplateConfig config = PromptTemplateConfig.builder()
            .withName(name)
            .withTemplate(template)
            .withTemplateFormat(templateFormat)
            .withDescription(description)
            .withInputVariables(kernelInputVariables)
            .withOutputVariable(kernelOutputVariable)
            .withExecutionSettings(executionSettings)
            .build();

        assertEquals(PromptTemplateConfig.CURRENT_SCHEMA, config.getSchema());
        assertEquals(name, config.getName());
        assertEquals(template, config.getTemplate());
        assertEquals(templateFormat, config.getTemplateFormat());
        assertEquals(description, config.getDescription());
        assertEquals(kernelInputVariables, config.getInputVariables());
        assertEquals(kernelOutputVariable, config.getOutputVariable());
        assertEquals(executionSettings, config.getExecutionSettings());

    }

    @Test
    void testParseFromJson() throws Exception {

        String name = "a name";
        String description = "a description";
        String template = "A template for testing {{plugin.function input}}";
        String templateFormat = "semantic-kernel";
        List<KernelInputVariable> kernelInputVariables = Arrays.asList(
            new KernelInputVariable("input", "java.lang.String", "a description", "default value",
                true));
        KernelOutputVariable kernelOutputVariable = new KernelOutputVariable("java.lang.String",
            "a description");
        HashMap<String, PromptExecutionSettings> executionSettings = new HashMap<String, PromptExecutionSettings>() {
            {
                put("default", PromptExecutionSettings.builder().build());
            }
        };

        PromptTemplateConfig expected = PromptTemplateConfig.builder()
            .withName(name)
            .withTemplate(template)
            .withTemplateFormat(templateFormat)
            .withDescription(description)
            .withInputVariables(kernelInputVariables)
            .withOutputVariable(kernelOutputVariable)
            .withExecutionSettings(executionSettings)
            .build();

        String jsonString = "{"
            + "\"name\":\"" + name + "\","
            + "\"description\":\"" + description + "\","
            + "\"template\":\"" + template + "\","
            + "\"template_format\":\"" + templateFormat + "\","
            + "\"input_variables\":["
            + "{"
            + "\"name\":\"input\","
            + "\"type\":\"java.lang.String\","
            + "\"description\":\"a description\","
            + "\"defaultValue\":\"default value\","
            + "\"is_required\":true"
            + "}"
            + "],"
            + "\"output_variable\":{"
            + "\"type\":\"java.lang.String\","
            + "\"description\":\"a description\""
            + "},"
            + "\"executionSettings\":{"
            + "\"default\":{}"
            + "}"
            + "}";

        PromptTemplateConfig result = PromptTemplateConfig.parseFromJson(jsonString);
        assertEquals(expected, result);
    }
}
