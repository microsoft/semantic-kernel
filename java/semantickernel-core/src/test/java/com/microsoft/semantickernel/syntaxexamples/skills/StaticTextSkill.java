// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.syntaxexamples.skills;

import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters;

import reactor.core.publisher.Mono;

import java.util.Locale;

public class StaticTextSkill {

    @DefineSKFunction(description = "Change all string chars to uppercase.", name = "Uppercase")
    public static Mono<String> uppercase(
            @SKFunctionParameters(
                            description = "Text to uppercase",
                            name = "input",
                            defaultValue = "",
                            type = String.class)
                    String text) {
        return Mono.just(text.toUpperCase(Locale.ROOT));
    }

    @DefineSKFunction(description = "Append the day variable", name = "appendDay")
    public Mono<String> appendDay(
            @SKFunctionParameters(
                            description = "Text to append to",
                            name = "input",
                            defaultValue = "",
                            type = String.class)
                    String input,
            @SKFunctionParameters(
                            description = "Current day",
                            name = "day",
                            defaultValue = "",
                            type = String.class)
                    String day) {
        return Mono.just(input + day);
    }
}
