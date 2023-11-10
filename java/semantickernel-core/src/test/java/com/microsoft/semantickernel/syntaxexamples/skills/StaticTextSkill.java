// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.syntaxexamples.skills;

import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionInputAttribute;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters;
import java.util.Locale;
import reactor.core.publisher.Mono;

public class StaticTextSkill {

    @DefineSKFunction(description = "Change all string chars to uppercase.", name = "Uppercase")
    public static Mono<String> uppercase(
            @SKFunctionInputAttribute(description = "Text to uppercase") String text) {
        return Mono.just(text.toUpperCase(Locale.ROOT));
    }

    @DefineSKFunction(description = "Append the day variable", name = "appendDay")
    public Mono<String> appendDay(
            @SKFunctionInputAttribute(description = "Text to append to") String input,
            @SKFunctionParameters(description = "Current day", name = "day") String day) {
        return Mono.just(input + day);
    }
}
