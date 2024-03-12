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
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;

import com.microsoft.semantickernel.plugin.KernelReturnParameterMetadata;

public class KernelFunctionFromMethodTest {

    public KernelFunctionFromMethodTest() {
    }

    @Test
    void testCreate() throws Exception {
        Method method = String.class.getMethod("concat", String.class);
        String pluginName = "test-plugin";
        String functionName = "concat";
        String description = "concatenate two strings";
        List<KernelParameterMetadata<?>> parameters = Arrays.asList(new KernelParameterMetadata<>("string1", "first string to concatenate", String.class, null, true));
        KernelReturnParameterMetadata<String> returnParameter = new KernelReturnParameterMetadata<>("concatenated strings", String.class);
        KernelFunction<?> result = KernelFunctionFromMethod.create(method, "test", pluginName, functionName, description, parameters, returnParameter);
        assertEquals(functionName, result.getName());
        assertEquals(pluginName, result.getPluginName());
        assertEquals(description, result.getDescription());
        assertEquals(parameters, result.getMetadata().getParameters());
        assertEquals(returnParameter, result.getMetadata().getReturnParameter());
    }

    /**
     * Test of builder method, of class KernelFunctionFromMethod.
     */
    @Test
    void testBuilder() {
        String pluginName = null;
        String functionName = "concat";
        String description = "concatenate two strings";
        List<InputVariable> parameters = Arrays.asList(new InputVariable("string1", "java.lang.String", "first string to concatenate", null, true));
        OutputVariable returnParameter = new OutputVariable("java.lang.String", "concatenated strings");
        KernelFunction<String> result = new KernelFunctionFromPrompt.Builder<String>()
                .withName(functionName)
                .withDescription(description)
                .withInputParameters(parameters)
                .withOutputVariable(returnParameter)
                .withPromptTemplate((kernel, args, context) -> null)
                .build();
        assertEquals(functionName, result.getName());
        assertEquals(pluginName, result.getPluginName());
        assertEquals(description, result.getDescription());
        // TODO: This assert fails because getParameters is a List<KernelParameterMetadata<?>>, not an List<InputVariable>
        //       This feels like it's broken. Until this is fixed, we can compare the types
        // assertEquals(parameters, result.getMetadata().getParameters());
        assertEquals(parameters.size(), result.getMetadata().getParameters().size());
        for (int i = 0; i < parameters.size(); i++) {
            assertEquals(parameters.get(i).getDescription(), result.getMetadata().getParameters().get(i).getDescription());
            assertEquals(parameters.get(i).getName(), result.getMetadata().getParameters().get(i).getName());
            // TODO: InputVariable.getType() returns a String, but KernelParameterMetadata.getType() returns a Class<?>
            //      This feels like it's broken, especially since OuputVariable.getType() returns a Class<?>
            //      Until this is fixed, we can compare the class names
            // assertEquals(parameters.get(i).getType(), result.getMetadata().getParameters().get(i).getType());
            assertEquals(parameters.get(i).getType(), result.getMetadata().getParameters().get(i).getType().getName());
            assertEquals(parameters.get(i).isRequired(), result.getMetadata().getParameters().get(i).isRequired());
        }
        // TODO: This assert fails because getReturnParameter is a KernelReturnParameterMetadata, not an OutputVariable
        //       This feels like it's broken. Until this is fixed, we can compare the types
        // assertEquals(returnParameter, result.getMetadata().getReturnParameter());
        assertEquals(returnParameter.getType(), result.getMetadata().getReturnParameter().getParameterType());
        assertEquals(returnParameter.getDescription(), result.getMetadata().getReturnParameter().getDescription());
    }

    /**
     * Test of invokeAsync method, of class KernelFunctionFromMethod.
     */
    @Test @Disabled("TODO: needs mocked http server")
    void testInvokeAsync() {
    }

}