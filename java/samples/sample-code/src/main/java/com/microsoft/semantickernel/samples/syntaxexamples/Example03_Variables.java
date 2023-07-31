// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.syntaxexamples;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.orchestration.ContextVariables;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.skilldefinition.ReadOnlyFunctionCollection;
import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionInputAttribute;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters;
import reactor.core.publisher.Mono;

import java.util.Locale;

public class Example03_Variables {

    public static class StaticTextSkill {
        @DefineSKFunction(description = "Change all string chars to uppercase.", name = "Uppercase")
        public static Mono<String> uppercase(
                @SKFunctionInputAttribute(description = "Text to uppercase")
                String text) {
            return Mono.just(text.toUpperCase(Locale.ROOT));
        }

        @DefineSKFunction(description = "Append the day variable", name = "appendDay")
        public Mono<String> appendDay(
                @SKFunctionInputAttribute(description = "Text to append to")
                String input,
                @SKFunctionParameters(description = "Current day", name = "day") String day) {
            return Mono.just(input + day);
        }
    }

    public static void main(String[] args) {
        Kernel kernel = SKBuilders.kernel().build();

        // Load native skill
        ReadOnlyFunctionCollection functionCollection =
                kernel.importSkill(new StaticTextSkill(), "text");

        ContextVariables variables =
                SKBuilders.variables()
                        .build("Today is: ")
                        .writableClone()
                        .setVariable("day", "Monday");

        Mono<SKContext> result =
                kernel.runAsync(
                        variables,
                        functionCollection.getFunction("AppendDay"),
                        functionCollection.getFunction("Uppercase"));

        System.out.println(result.block().getResult());
    }
}
