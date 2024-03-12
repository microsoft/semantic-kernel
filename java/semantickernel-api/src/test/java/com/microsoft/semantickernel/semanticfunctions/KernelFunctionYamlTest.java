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

import java.nio.file.Path;
import java.util.Arrays;
import java.util.HashMap;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.fail;
import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;

import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;

/**
 *
 * @author davidgrieve
 */
public class KernelFunctionYamlTest {

    @Test
    public void testFromPromptYamlWithSemanticKernelTemplate() throws Exception {
        testFromPromptYaml("semantic-kernel");
    }

    @Test
    public void testFromPromptYamlWithHandleBarsTemplate() throws Exception {
        testFromPromptYaml("handlebars");
    }

    private void testFromPromptYaml(String templateFormat) throws Exception {
      String yaml = String.format("name: GenerateStory\n" +
        "template: |\n" +
        "  Tell a story about {{$topic}} that is {{$length}} sentences long.\n" +
        "template_format: %s\n" +
        "description: A function that generates a story about a topic.\n" +
        "input_variables:\n" +
        "  - name: topic\n" +
        "    description: The topic of the story.\n" +
        "    is_required: true\n" +
        "  - name: length\n" +
        "    description: The number of sentences in the story.\n" +
        "    is_required: true\n" +
        "output_variable:\n" +
        "  description: The generated story.\n" +
        "execution_settings:\n" +
        "  default:\n" +
        "    temperature: 0.6", templateFormat);
        @SuppressWarnings({ "rawtypes", "unchecked" })
        KernelFunction<?> expResult = new KernelFunctionFromPrompt.Builder()
            .withName("GenerateStory")
            .withTemplate("Tell a story about {{$topic}} that is {{$length}} sentences long.")
            .withTemplateFormat(templateFormat)
            .withDescription("A function that generates a story about a topic.")
            .withInputParameters(Arrays.asList(
                new InputVariable(
                    "topic",
                    "java.lang.String",
                    "The topic of the story.",
                    null,
                    true
                ),
                new InputVariable(
                    "length",
                    "java.lang.String",
                    "The number of sentences in the story.",
                    null,
                    true
                )
            ))
            .withOutputVariable("The generated story.", "java.lang.String")
            .withExecutionSettings(new HashMap() {{
                put("default", PromptExecutionSettings.builder()
                    .withTemperature(0.6)
                    .build()
                );
            }})
            .build();

        KernelFunction<?> result = KernelFunctionYaml.fromPromptYaml(yaml);
        assertNotNull(result);
        assertEquals(expResult.getName(), result.getName());
        assertEquals(expResult.getDescription(), result.getDescription());
        assertEquals(expResult.getExecutionSettings(), result.getExecutionSettings());
        assertEquals(expResult.getMetadata(), result.getMetadata());
    }

    /**
     * Test of fromYaml method, of class KernelFunctionYaml.
     */
    @Test @Disabled
    public void testFromYaml() throws Exception {
        System.out.println("fromYaml");
        Path filePath = null;
        KernelFunction expResult = null;
        KernelFunction result = KernelFunctionYaml.fromYaml(filePath);
        assertEquals(expResult, result);
        // TODO review the generated test code and remove the default call to fail.
        fail("The test case is a prototype.");
    }

}