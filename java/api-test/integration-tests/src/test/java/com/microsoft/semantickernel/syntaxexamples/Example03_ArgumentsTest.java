// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.syntaxexamples;

import com.microsoft.semantickernel.DefaultKernel;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.samples.syntaxexamples.Example03_Arguments.StaticTextSkill;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

/**
 * Demonstrates running a pipeline (a sequence of functions) on a
 * {@code com.microsoft.semantickernel.orchestration.SKContext}
 */
public class Example03_ArgumentsTest {

    @Test
    public void main() {
        Kernel kernel = new DefaultKernel.Builder().build();

        // Load native skill
        KernelPlugin functionCollection =
            KernelPluginFactory.createFromObject(new StaticTextSkill(), "text");

        KernelArguments arguments = KernelArguments.builder()
            .withInput("Today is: ")
            .build()
            .writableClone()
            .setVariable("day", "Monday");

        ContextVariable<String> resultValue = kernel.invokeAsync(
                functionCollection.get("AppendDay"),
                arguments,
                String.class)
            .block();

        Assertions.assertEquals("Today is: Monday", resultValue.getValue());
    }
}
