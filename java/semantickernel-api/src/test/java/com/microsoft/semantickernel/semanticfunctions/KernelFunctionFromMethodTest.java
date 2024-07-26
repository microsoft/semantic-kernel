// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

import static org.junit.jupiter.api.Assertions.assertEquals;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.contextvariables.ContextVariableTypes;
import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.semanticfunctions.annotations.DefineKernelFunction;
import com.microsoft.semantickernel.semanticfunctions.annotations.KernelFunctionParameter;
import java.lang.reflect.Method;
import java.util.Collections;
import java.util.List;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;
import reactor.core.publisher.Mono;

public class KernelFunctionFromMethodTest {

    public KernelFunctionFromMethodTest() {
    }

    public static class ExamplePlugin {

        @DefineKernelFunction(name = "sqrt", description = "Take the square root of a number")
        public static double sqrt(
            @KernelFunctionParameter(name = "number1", description = "The number to take a square root of", type = double.class) double number1) {
            return Math.sqrt(number1);
        }
    }

    @Test
    void typeConversionOnMethodCall() {
        KernelPlugin plugin = KernelPluginFactory.createFromObject(
            new ExamplePlugin(), "ExamplePlugin");

        Kernel kernel = Kernel.builder().build();

        FunctionResult<String> result = plugin
            .get("sqrt")
            .invokeAsync(kernel)
            .withResultType(ContextVariableTypes.getGlobalVariableTypeForClass(String.class))
            .withArguments(
                KernelFunctionArguments.builder()
                    .withVariable("number1", "12.0")
                    .build())
            .block();

        Assertions.assertEquals("3.4641016151377544", result.getResult());
    }

    @Test
    void testCreate() throws Exception {
        Method method = String.class.getMethod("concat", String.class);
        String pluginName = "test-plugin";
        String functionName = "concat";
        String description = "concatenate two strings";
        List<InputVariable> parameters = Collections.singletonList(InputVariable.build(
            "string1", String.class, "first string to concatenate", null, null, true));
        OutputVariable<String> returnParameter = new OutputVariable<>(
            "concatenated strings", String.class);
        KernelFunction<?> result = KernelFunctionFromMethod.create(method, "test", pluginName,
            functionName, description, parameters, returnParameter);
        assertEquals(functionName, result.getName());
        assertEquals(pluginName, result.getPluginName());
        assertEquals(description, result.getDescription());
        assertEquals(parameters, result.getMetadata().getParameters());
        assertEquals(returnParameter, result.getMetadata().getOutputVariableType());
    }

    /**
     * Test of builder method, of class KernelFunctionFromMethod.
     */
    @Test
    void testBuilder() {
        String pluginName = null;
        String functionName = "concat";
        String description = "concatenate two strings";
        List<InputVariable> parameters = Collections
            .singletonList(new InputVariable("string1",
                "java.lang.String", "first string to concatenate", null, true, null));
        OutputVariable<?> returnParameter = new OutputVariable<>("java.lang.String",
            "concatenated strings");
        KernelFunction<String> result = new KernelFunctionFromPrompt.Builder()
            .withName(functionName)
            .withDescription(description)
            .withInputParameters(parameters)
            .withOutputVariable(returnParameter)
            .withPromptTemplate((kernel, args, context) -> Mono.empty())
            .build();
        assertEquals(functionName, result.getName());
        assertEquals(pluginName, result.getPluginName());
        assertEquals(description, result.getDescription());
        // TODO: This assert fails because getParameters is a List<KernelParameterMetadata<?>>, not an List<InputVariable>
        //       This feels like it's broken. Until this is fixed, we can compare the types
        // assertEquals(parameters, result.getMetadata().getParameters());
        assertEquals(parameters.size(), result.getMetadata().getParameters().size());
        for (int i = 0; i < parameters.size(); i++) {
            assertEquals(parameters.get(i).getDescription(),
                result.getMetadata().getParameters().get(i).getDescription());
            assertEquals(parameters.get(i).getName(),
                result.getMetadata().getParameters().get(i).getName());
            assertEquals(parameters.get(i).getType(),
                result.getMetadata().getParameters().get(i).getType());
            assertEquals(parameters.get(i).isRequired(),
                result.getMetadata().getParameters().get(i).isRequired());
        }
        assertEquals(returnParameter, result.getMetadata().getOutputVariableType());
        assertEquals(returnParameter.getType(),
            result.getMetadata().getOutputVariableType().getType());
        assertEquals(returnParameter.getDescription(),
            result.getMetadata().getOutputVariableType().getDescription());
    }

    /**
     * Test of invokeAsync method, of class KernelFunctionFromMethod.
     */
    @Test
    @Disabled("TODO: needs mocked http server")
    void testInvokeAsync() {
    }

}