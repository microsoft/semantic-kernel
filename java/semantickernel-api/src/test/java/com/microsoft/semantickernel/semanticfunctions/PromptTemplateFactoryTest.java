/*
 * The MIT License
 *
 * Copyright 2024 davidgrieve.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */

package com.microsoft.semantickernel.semanticfunctions;

import java.lang.reflect.Method;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.contextvariables.ContextVariable;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.plugin.KernelReturnParameterMetadata;
import com.microsoft.semantickernel.semanticfunctions.annotations.DefineKernelFunction;
import com.microsoft.semantickernel.semanticfunctions.annotations.KernelFunctionParameter;
 
public class PromptTemplateFactoryTest {

    @DefineKernelFunction(name = "function", description = "a function")
    public String function(
        @KernelFunctionParameter(name = "input", description = "the input", type = String.class) String input) {
        return String.format("plugin function received: %s", input);
    }

    @Test 
    void createPromptTemplateFromHandlebarsConfig() throws Exception  {
        executeTest("handlebars");
    }

    @Test 
    void createPromptTemplateFromDefaultConfig() throws Exception  {
        executeTest("semantic-kernel");
    }

    private void executeTest(String templateFormat) throws Exception {
        
        Method method = PromptTemplateFactoryTest.class.getMethod("function", String.class);
        List<KernelParameterMetadata<?>> parameters = Arrays.asList(new KernelParameterMetadata<>("input", "the input", String.class, "borked", true));
        KernelReturnParameterMetadata<String> returnParameter = new KernelReturnParameterMetadata<>("the output", String.class);
        KernelFunction<?> function = KernelFunctionFromMethod.create(
            method, 
            this, 
            "plugin",
            "function",
            "this is plugin.function",
            parameters, 
            returnParameter
        );

        Kernel kernel = Kernel.builder()
            .withPlugin(new KernelPlugin(
                "plugin", 
                "a plugin", 
                new HashMap<String,KernelFunction<?>>() {{ put("function", function); }})
            )
            .build();

        String name = "a name";
        String description = "a description";
        String template = "semantic-kernel".equals(templateFormat) 
            ? "A template for testing: {{plugin.function $input}}"
            : "A template for testing: {{plugin-function input}}";
        List<InputVariable> inputVariables = Arrays.asList(
            new InputVariable("input", "java.lang.String", "a description", "input from config", true)
        );
        OutputVariable outputVariable = new OutputVariable("java.lang.String", "a description");
        HashMap<String, PromptExecutionSettings> executionSettings = new HashMap<String, PromptExecutionSettings>() {{
            put("default", PromptExecutionSettings.builder().build());
        }};
    
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
        
        String expected = String.format("A template for testing: %s", function((String)args.getInput().getValue()));
        String renderedPrompt = promptTemplate.renderAsync(kernel, args, null).block();
        assertEquals(expected, renderedPrompt);
    }
}