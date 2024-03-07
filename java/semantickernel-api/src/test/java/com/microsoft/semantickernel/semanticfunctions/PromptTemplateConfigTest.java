package com.microsoft.semantickernel.semanticfunctions;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.util.Arrays;
import java.util.HashMap;
import java.util.List;

import org.junit.jupiter.api.Test;

import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;

public class PromptTemplateConfigTest {
    
    @Test
    void testInstanceMadeWithBuilderEqualsInstanceMadeWithConstructor() {
        String name = "a name";
        String description = "a description";
        String template = "A template for testing {{plugin.function input}}";
        List<InputVariable> inputVariables = Arrays.asList(
            new InputVariable("input", "java.lang.String", "a description", "default value", true)
        );
        OutputVariable outputVariable = new OutputVariable("java.lang.String", "a description");

        PromptTemplateConfig expected = new PromptTemplateConfig(
            PromptTemplateConfig.CURRENT_SCHEMA,
            name,
            template,
            "semantic-kernel",
            description,
            inputVariables,
            outputVariable,
            new HashMap<String, PromptExecutionSettings>() {{
                put("default", PromptExecutionSettings.builder().build());
            }}
        );

        PromptTemplateConfig result = PromptTemplateConfig.builder()
                .withName(name)
                .withDescription(description)
                .withTemplate(template)
                .withInputVariables(inputVariables)
                .withOutputVariable(outputVariable)
                .withExecutionSettings(new HashMap<String, PromptExecutionSettings>() {{
                    put("default", PromptExecutionSettings.builder().build());
                }})    
                .build();

        assertEquals(expected, result);
    }

    @Test
    void testDefaultTemplateBuilder() {

    }

    @Test
    void testParseFromJson() {

    }
}
