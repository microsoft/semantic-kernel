// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.syntaxexamples;

import java.util.Locale;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.orchestration.KernelFunctionArguments;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.plugin.annotations.DefineKernelFunction;
import com.microsoft.semantickernel.plugin.annotations.KernelFunctionParameter;

import reactor.core.publisher.Mono;

/**
 * Demonstrates running a pipeline (a sequence of functions) on a
 * {@code com.microsoft.semantickernel.orchestration.SKContext}
 */
public class Example03_Arguments {

    public static class StaticTextSkill {
        @DefineKernelFunction(
            description = "Change all string chars to uppercase.",
            name = "Uppercase")
        public static Mono<String> uppercase(
            @KernelFunctionParameter(
                description = "Text to uppercase",
                name = "input")
            String text) {
            return Mono.just(text.toUpperCase(Locale.ROOT));
        }

        @DefineKernelFunction(description = "Append the day variable", name = "appendDay")
        public Mono<String> appendDay(
            @KernelFunctionParameter(description = "Text to append to", name = "input")
            String input,
            @KernelFunctionParameter(description = "Current day", name = "day") String day) {
            return Mono.just(input + day);
        }
    }

    public static void main(String[] args) {
        Kernel kernel = Kernel.builder().build();

        // Load native skill
        KernelPlugin functionCollection =
            KernelPluginFactory.createFromObject(new StaticTextSkill(), "text");

        KernelFunctionArguments arguments = KernelFunctionArguments.builder()
            .withInput("Today is: ")
            .withVariable("day", "Monday")
            .build();

        FunctionResult<String> resultValue = kernel.invokeAsync(
                functionCollection.get("AppendDay"),
                arguments,
                String.class)
            .block();

        System.out.println(resultValue.getResultVariable());
    }
}
