package com.microsoft.semantickernel.samples.syntaxexamples;

import com.microsoft.semantickernel.samples.plugins.text.TextPlugin;

/**
 * Demonstrates a native function from the {@code com.microsoft.semantickernel.coreskills} package.
 */
public class Example01_NativeFunctions {

    public static void main(String[] args) {

        // Load native skill
        TextPlugin text = new TextPlugin();

        // Use function without kernel
        String result = text.uppercase("ciao!");

        System.out.println(result);
    }
}
