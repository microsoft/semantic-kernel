// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.tests;

import com.microsoft.semantickernel.semanticfunctions.annotations.DefineKernelFunction;
import com.microsoft.semantickernel.semanticfunctions.annotations.KernelFunctionParameter;

import java.util.Locale;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

public class Example01NativeFunctionsTest {

    private static class TextPlugin {

        @DefineKernelFunction(description = "Change all string chars to uppercase.", name = "Uppercase")
        public String uppercase(
            @KernelFunctionParameter(description = "Text to uppercase", name = "input") String text) {
            return text.toUpperCase(Locale.ROOT);
        }

    }

    @Test
    public void run() {
        // Load native plugin
        TextPlugin text = new TextPlugin();

        // Use function without kernel
        String result = text.uppercase("ciao!");

        Assertions.assertEquals("CIAO!", result);
    }
}
