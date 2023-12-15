// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.plugins;

import com.microsoft.semantickernel.plugin.annotations.DefineKernelFunction;
import com.microsoft.semantickernel.plugin.annotations.KernelFunctionParameter;
import java.util.Locale;

/**
 * TextSkill provides a set of functions to manipulate strings.
 */
public class TextPlugin {

    @DefineKernelFunction(description = "Change all string chars to uppercase.", name = "Uppercase")
    public String uppercase(
        @KernelFunctionParameter(
            description = "Text to uppercase",
            name = "input") String text) {
        return text.toUpperCase(Locale.ROOT);
    }

    @DefineKernelFunction(description = "Remove spaces to the left of a string.", name = "LStrip")
    public String lStrip(@KernelFunctionParameter(description = "Text to edit",
        name = "input") String text) {
        return text.replaceAll("^ +", "");
    }

    @DefineKernelFunction(description = "Remove spaces to the right of a string.", name = "RStrip")
    public String rStrip(@KernelFunctionParameter(description = "Text to edit",
        name = "input") String text) {
        return text.replaceAll(" +$", "");
    }

    @DefineKernelFunction(
        description = "Remove spaces to the left and right of a string",
        name = "Strip")
    public String strip(@KernelFunctionParameter(description = "Text to edit",
        name = "input") String input) {
        return input.trim();
    }

    @DefineKernelFunction(description = "Change all string chars to lowercase", name = "lowercase")
    public String lowercase(
        @KernelFunctionParameter(description = "Text to lowercase",
            name = "input") String input) {
        return input.toLowerCase(Locale.ROOT);
    }
}
