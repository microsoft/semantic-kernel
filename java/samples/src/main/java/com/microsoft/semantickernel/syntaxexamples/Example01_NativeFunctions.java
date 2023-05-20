package com.microsoft.semantickernel.syntaxexamples;

import com.microsoft.semantickernel.coreskills.TextSkill;

public class Example01_NativeFunctions {

    public static void main(String[] args) {

        // Load native skill
        TextSkill text = new TextSkill();

        // Use function without kernel
        String result = text.uppercase("ciao!").block();

        System.out.println(result);
    }
}
