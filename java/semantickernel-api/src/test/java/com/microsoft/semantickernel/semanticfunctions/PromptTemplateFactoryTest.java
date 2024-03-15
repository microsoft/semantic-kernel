// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

import static org.junit.jupiter.api.Assertions.assertEquals;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.contextvariables.ContextVariable;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.semanticfunctions.annotations.DefineKernelFunction;
import com.microsoft.semantickernel.semanticfunctions.annotations.KernelFunctionParameter;
import java.lang.reflect.Method;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import javax.annotation.Nullable;
import org.junit.jupiter.api.Test;

@SuppressWarnings("DoubleBraceInitialization")
public class PromptTemplateFactoryTest {

    @DefineKernelFunction(name = "function", description = "a function")
    public String function(
        @Nullable @KernelFunctionParameter(name = "input", description = "the input", type = String.class) String input) {
        return String.format("plugin function received: %s", input);
    }

    @Test
    void createPromptTemplateFromHandlebarsConfig() throws Exception {
        executeTest("handlebars");
    }

    @Test
    void createPromptTemplateFromDefaultConfig() throws Exception {
        executeTest("semantic-kernel");
    }

    private void executeTest(String templateFormat) throws Exception {

        Method method = PromptTemplateFactoryTest.class.getMethod("function", String.class);
        List<InputVariable> parameters = Collections.singletonList(
            new InputVariable("input", String.class.getName(), "the input", "borked",
                true));
        OutputVariable<String> returnParameter = new OutputVariable<>(
            "the output", String.class);
        KernelFunction<?> function = KernelFunctionFromMethod.create(
            method,
            this,
            "plugin",
            "function",
            "this is plugin.function",
            parameters,
            returnParameter);

        Kernel kernel = Kernel.builder()
            .withPlugin(new KernelPlugin(
                "plugin",
                "a plugin",
                new HashMap<String, KernelFunction<?>>() {
                    {
                        put("function", function);
                    }
                }))
            .build();

        String name = "a name";
        String description = "a description";
        String template = "semantic-kernel".equals(templateFormat)
            ? "A template for testing: {{plugin.function $input}}"
            : "A template for testing: {{plugin-function input}}";
        List<InputVariable> inputVariables = Arrays.asList(
            new InputVariable("input", "java.lang.String", "a description",
                "input from config",
                true));
        OutputVariable outputVariable = new OutputVariable("java.lang.String",
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
            .withInputVariables(inputVariables)
            .withOutputVariable(outputVariable)
            .withExecutionSettings(executionSettings)
            .build();

        PromptTemplate promptTemplate = PromptTemplateFactory.build(config);

        KernelFunctionArguments args = KernelFunctionArguments.builder()
            .withInput(ContextVariable.of("input from args")).build();

        String expected = String.format("A template for testing: %s",
            function((String) args.getInput().getValue()));
        String renderedPrompt = promptTemplate.renderAsync(kernel, args, null).block();
        assertEquals(expected, renderedPrompt);
    }
}