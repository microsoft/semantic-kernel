// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.KernelConfig;
import com.microsoft.semantickernel.SamplesConfig;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.exceptions.ConfigurationException;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionInputAttribute;
import com.microsoft.semantickernel.textcompletion.TextCompletion;
import reactor.core.publisher.Mono;

import java.time.Duration;

public class Example09_FunctionTypes {
    public static void main(String[] args) throws ConfigurationException {
        OpenAIAsyncClient client = SamplesConfig.getClient();

        TextCompletion textCompletion = SKBuilders.textCompletionService().build(client, "text-davinci-003");

        KernelConfig kernelConfig = new KernelConfig.Builder()
                .addTextCompletionService("text-davinci-003", kernel -> textCompletion)
                .build();

        Kernel kernel = SKBuilders.kernel().withKernelConfig(kernelConfig).build();

        System.out.println("======== Native function types ========");

        // Load native skill into the kernel skill collection, sharing its functions with prompt templates
        var test = kernel
                .importSkill(new LocalExampleSkill(), "test");

        kernel.importSkillsFromDirectory(SampleSkillsUtil.detectSkillDirLocation(), "SummarizeSkill");


        var fakeContext = SKBuilders.context()
                .with(kernel.getSkills())
                .build();

        // The kernel takes care of wiring the input appropriately
        SKContext result = kernel.runAsync(
                        "",
                        test.getFunction("type01"),
                        test.getFunction("type02"),
                        test.getFunction("type03"),
                        test.getFunction("type04"),
                        test.getFunction("type05"),
                        test.getFunction("type06"),
                        test.getFunction("type07"),
                        test.getFunction("type08"),
                        test.getFunction("type09"),
                        test.getFunction("type10"),
                        test.getFunction("type11"),
                        test.getFunction("type12"),
                        test.getFunction("type13"),
                        test.getFunction("type14"),
                        test.getFunction("type15"),
                        test.getFunction("type16"),
                        test.getFunction("type17"),
                        test.getFunction("type18")
                )
                .block();

        kernel.getFunction("test", "type01").invokeAsync().block();
        test.getFunction("type01").invokeAsync().block();

        kernel.getFunction("test", "type02").invokeAsync().block();
        test.getFunction("type02").invokeAsync().block();

        kernel.getFunction("test", "type03").invokeAsync().block();
        test.getFunction("type03").invokeAsync().block();

        kernel.getFunction("test", "type04").invokeAsync(fakeContext).block();
        test.getFunction("type04").invokeAsync(fakeContext).block();

        kernel.getFunction("test", "type05").invokeAsync(fakeContext).block();
        test.getFunction("type05").invokeAsync(fakeContext).block();

        kernel.getFunction("test", "type06").invokeAsync(fakeContext).block();
        test.getFunction("type06").invokeAsync(fakeContext).block();

        kernel.getFunction("test", "type07").invokeAsync(fakeContext).block();
        test.getFunction("type07").invokeAsync(fakeContext).block();

        kernel.getFunction("test", "type08").invokeAsync("").block();
        test.getFunction("type08").invokeAsync("").block();

        kernel.getFunction("test", "type09").invokeAsync("").block();
        test.getFunction("type09").invokeAsync("").block();

        kernel.getFunction("test", "type10").invokeAsync("").block();
        test.getFunction("type10").invokeAsync("").block();

        kernel.getFunction("test", "type11").invokeAsync("").block();
        test.getFunction("type11").invokeAsync("").block();

        kernel.getFunction("test", "type12").invokeAsync("").block();
        test.getFunction("type12").invokeAsync("").block();

        kernel.getFunction("test", "type13").invokeAsync("").block();
        test.getFunction("type13").invokeAsync("").block();

        kernel.getFunction("test", "type14").invokeAsync("").block();
        test.getFunction("type14").invokeAsync("").block();

        kernel.getFunction("test", "type15").invokeAsync("").block();
        test.getFunction("type15").invokeAsync("").block();

        kernel.getFunction("test", "type16").invokeAsync("").block();
        test.getFunction("type16").invokeAsync("").block();

        kernel.getFunction("test", "type17").invokeAsync("").block();
        test.getFunction("type17").invokeAsync("").block();

        kernel.getFunction("test", "type18").invokeAsync("").block();
        test.getFunction("type18").invokeAsync("").block();
    }


    public static class LocalExampleSkill {

        @DefineSKFunction(name = "type01")
        public void Type01() {
            System.out.println("Running function type 1");
        }

        @DefineSKFunction(name = "type02")
        public String Type02() {
            System.out.println("Running function type 2");
            return "";
        }

        @DefineSKFunction(name = "type03")
        public Mono<String> Type03Async() {
            return Mono.delay(Duration.ZERO)
                    .map(x -> {
                        System.out.println("Running function type 3");
                        return "";
                    });
        }


        @DefineSKFunction(name = "type04")
        public void Type04(SKContext context) {
            System.out.println("Running function type 4");
        }


        @DefineSKFunction(name = "type05")
        public String Type05(SKContext context) {
            System.out.println("Running function type 5");
            return "";
        }


        @DefineSKFunction(name = "type06")
        public Mono<String> Type06Async(SKContext context) {
            var summarizer = context.getSkills().getFunction("SummarizeSkill", "Summarize", null);

            return summarizer
                    .invokeAsync("blah blah blah")
                    .map(summary -> {
                        System.out.println("Running function type 6 " + summary.getResult());
                        return "";
                    });
        }

        @DefineSKFunction(name = "type07")
        public Mono<SKContext> Type07Async(SKContext context) {
            return Mono.delay(Duration.ZERO)
                    .map(x -> {
                        System.out.println("Running function type 7");
                        return context;
                    });
        }

        @DefineSKFunction(name = "type08")
        public void Type08(
                @SKFunctionInputAttribute
                String x) {
            System.out.println("Running function type 8");
        }


        @DefineSKFunction(name = "type09")
        public String Type09(
                @SKFunctionInputAttribute
                String x) {
            System.out.println("Running function type 9");
            return "";
        }

        @DefineSKFunction(name = "type10")
        public Mono<String> Type10Async(
                @SKFunctionInputAttribute
                String x) {
            return Mono.delay(Duration.ZERO)
                    .map(x2 -> {
                        System.out.println("Running function type 10");
                        return "";
                    });
        }

        @DefineSKFunction(name = "type11")
        public void Type11(
                @SKFunctionInputAttribute
                String x,
                SKContext context) {
            System.out.println("Running function type 11");
        }


        @DefineSKFunction(name = "type12")
        public String Type12(
                @SKFunctionInputAttribute
                String x,
                SKContext context) {
            System.out.println("Running function type 12");
            return "";
        }

        @DefineSKFunction(name = "type13")
        public Mono<String> Type13Async(
                @SKFunctionInputAttribute
                String x, SKContext context) {
            return Mono.delay(Duration.ZERO)
                    .map(x2 -> {
                        System.out.println("Running function type 13");
                        return "";
                    });
        }

        @DefineSKFunction(name = "type14")
        public Mono<SKContext> Type14Async(
                @SKFunctionInputAttribute
                String x, SKContext context) {
            return Mono.delay(Duration.ZERO)
                    .ignoreElement()
                    .map(x2 -> {
                        System.out.println("Running function type 14");
                        return context;
                    });
        }

        @DefineSKFunction(name = "type15")
        public Mono<Void> Type15Async(String x) {
            return Mono.delay(Duration.ZERO)
                    .ignoreElement()
                    .doFinally(ignore -> System.out.println("Running function type 15"))
                    .then();
        }

        @DefineSKFunction(name = "type16")
        public Mono<Void> Type16Async(SKContext context) {
            return Mono.delay(Duration.ZERO)
                    .ignoreElement()
                    .doFinally(ignore -> System.out.println("Running function type 16"))
                    .then();
        }

        @DefineSKFunction(name = "type17")
        public Mono<Void> Type17Async(String x, SKContext context) {
            return Mono.delay(Duration.ZERO)
                    .ignoreElement()
                    .doFinally(ignore -> System.out.println("Running function type 17"))
                    .then();
        }

        @DefineSKFunction(name = "type18")
        public Mono<Void> Type18Async() {
            return Mono.delay(Duration.ZERO)
                    .ignoreElement()
                    .doFinally(ignore -> System.out.println("Running function type 18"))
                    .then();
        }
    }
}
