// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.syntaxexamples;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.samples.syntaxexamples.Example03_Arguments.StaticTextPlugin;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

/**
 * Demonstrates running a pipeline (a sequence of functions) on a
 * {@code com.microsoft.semantickernel.orchestration.SKContext}
 */
public class Example03_ArgumentsTest {

    @Test
    public void main() {
        Kernel kernel = Kernel.builder().build();

        // Load native skill
        KernelPlugin functionCollection =
            KernelPluginFactory.createFromObject(new StaticTextPlugin(), "text");

        KernelArguments arguments = KernelArguments.builder()
            .withInput("Today is: ")
            .build()
            .writableClone()
            .setVariable("day", "Monday");

        FunctionResult<String> resultValue = kernel.invokeAsync(
                functionCollection.get("AppendDay"),
                arguments,
                String.class)
            .block();

        Assertions.assertEquals("Today is: Monday", resultValue.getResult());
    }
}
