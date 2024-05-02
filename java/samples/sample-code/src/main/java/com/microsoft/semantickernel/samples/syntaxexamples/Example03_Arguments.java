// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.syntaxexamples;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionArguments;
import com.microsoft.semantickernel.semanticfunctions.annotations.DefineKernelFunction;
import com.microsoft.semantickernel.semanticfunctions.annotations.KernelFunctionParameter;
import java.util.Locale;
import reactor.core.publisher.Mono;

/**
 * Demonstrates running a pipeline (a sequence of functions) on a
 * {@code com.microsoft.semantickernel.orchestration.SKContext}
 */
public class Example03_Arguments {

    public static void main(String[] args) {
        Kernel kernel = Kernel.builder().build();

        // Load native plugin
        KernelPlugin functionCollection = KernelPluginFactory
            .createFromObject(new StaticTextPlugin(), "text");

        KernelFunctionArguments arguments = KernelFunctionArguments.builder()
            .withInput("Today is: ")
            .withVariable("day", "Monday")
            .build();

        FunctionResult<?> resultValue = kernel.invokeAsync(functionCollection.get("AppendDay"))
            .withArguments(arguments)
            .block();

        System.out.println(resultValue.getResult());
    }

    public static class StaticTextPlugin {

        @DefineKernelFunction(description = "Change all string chars to uppercase.", name = "Uppercase", returnType = "java.lang.String")
        public static Mono<String> uppercase(
            @KernelFunctionParameter(description = "Text to uppercase", name = "input") String text) {
            return Mono.just(text.toUpperCase(Locale.ROOT));
        }

        @DefineKernelFunction(description = "Append the day variable", name = "appendDay", returnType = "java.lang.String")
        public Mono<String> appendDay(
            @KernelFunctionParameter(description = "Text to append to", name = "input") String input,
            @KernelFunctionParameter(description = "Current day", name = "day") String day) {
            return Mono.just(input + day);
        }
    }
}
