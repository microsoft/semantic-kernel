// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.syntaxexamples.skills; // Copyright (c) Microsoft. All rights
// reserved.

import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters;

import reactor.core.publisher.Mono;

import java.util.Locale;

/// <summary>
/// TextSkill provides a set of functions to manipulate strings.
/// </summary>
/// <example>
/// Usage: kernel.ImportSkill("text", new TextSkill());
///
/// Examples:
/// SKContext["input"] = "  hello world  "
/// {{text.trim $input}} => "hello world"
/// {{text.trimStart $input} => "hello world  "
/// {{text.trimEnd $input} => "  hello world"
/// SKContext["input"] = "hello world"
/// {{text.uppercase $input}} => "HELLO WORLD"
/// SKContext["input"] = "HELLO WORLD"
/// {{text.lowercase $input}} => "hello world"
/// </example>
public class TextSkill {

    @DefineSKFunction(description = "Change all string chars to uppercase.", name = "Uppercase")
    public Mono<String> uppercase(
            @SKFunctionParameters(
                            description = "Text to uppercase",
                            name = "input",
                            defaultValue = "",
                            type = String.class)
                    String text) {
        return Mono.just(text.toUpperCase(Locale.ROOT));
    }

    @DefineSKFunction(description = "Remove spaces to the left of a string.", name = "LStrip")
    public Mono<String> lStrip(
            @SKFunctionParameters(
                            description = "Text to edit",
                            name = "input",
                            defaultValue = "",
                            type = String.class)
                    String text) {
        return Mono.just(text.replaceAll("^ +", ""));
    }

    @DefineSKFunction(description = "Remove spaces to the right of a string.", name = "RStrip")
    public Mono<String> rStrip(
            @SKFunctionParameters(
                            description = "Text to edit",
                            name = "input",
                            defaultValue = "",
                            type = String.class)
                    String text) {
        return Mono.just(text.replaceAll(" +$", ""));
    }
    /*

    [SKFunction("Remove spaces to the left of a string")]
    [SKFunctionInput(Description = "Text to edit")]
    public string LStrip(string input)
    {
        return input.TrimStart();
    }

    [SKFunction("Remove spaces to the right of a string")]
    [SKFunctionInput(Description = "Text to edit")]
    public string RStrip(string input)
    {
        return input.TrimEnd();
    }

    [SKFunction("Remove spaces to the left and right of a string")]
    [SKFunctionInput(Description = "Text to edit")]
    public string Strip(string input)
    {
        return input.Trim();
    }

    [SKFunction("Change all string chars to uppercase")]
    [SKFunctionInput(Description = "Text to uppercase")]
    public string Uppercase(string input)
    {
        return input.ToUpperInvariant();
    }

    [SKFunction("Change all string chars to lowercase")]
    [SKFunctionInput(Description = "Text to lowercase")]
    [SuppressMessage("Globalization", "CA1308:Normalize strings to uppercase", Justification = "By design.")]
    public string Lowercase(string input)
    {
        return input.ToLowerInvariant();
    }
     */
}
