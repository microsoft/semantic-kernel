// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.coreskills;

import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionInputAttribute;

import java.util.Locale;

/** TextSkill provides a set of functions to manipulate strings. */
public class TextSkill {

    @DefineSKFunction(description = "Change all string chars to uppercase.", name = "Uppercase")
    public String uppercase(
            @SKFunctionInputAttribute(description = "Text to uppercase") String text) {
        return text.toUpperCase(Locale.ROOT);
    }

    @DefineSKFunction(description = "Remove spaces to the left of a string.", name = "LStrip")
    public String lStrip(@SKFunctionInputAttribute(description = "Text to edit") String text) {
        return text.replaceAll("^ +", "");
    }

    @DefineSKFunction(description = "Remove spaces to the right of a string.", name = "RStrip")
    public String rStrip(@SKFunctionInputAttribute(description = "Text to edit") String text) {
        return text.replaceAll(" +$", "");
    }

    @DefineSKFunction(
            description = "Remove spaces to the left and right of a string",
            name = "Strip")
    public String strip(@SKFunctionInputAttribute(description = "Text to edit") String input) {
        return input.trim();
    }

    @DefineSKFunction(description = "Change all string chars to lowercase", name = "lowercase")
    public String lowercase(
            @SKFunctionInputAttribute(description = "Text to lowercase") String input) {
        return input.toLowerCase(Locale.ROOT);
    }
}
