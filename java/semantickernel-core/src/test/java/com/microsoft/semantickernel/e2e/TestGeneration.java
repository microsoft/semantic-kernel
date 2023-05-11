// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.e2e;

import static com.azure.core.implementation.http.rest.RestProxyUtils.LOGGER;
import static com.microsoft.semantickernel.e2e.AbstractKernelTest.buildTextCompletionKernel;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.textcompletion.CompletionSKContext;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;

import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;

import reactor.core.publisher.Mono;

import java.io.File;
import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeoutException;

public class TestGeneration {

    @Test
    @Disabled("for manual execution")
    public void generateTests()
            throws IOException, ExecutionException, InterruptedException, TimeoutException {
        Kernel kernel = buildTextCompletionKernel();

        String fileName =
                "src/main/java/com/microsoft/semantickernel/connectors/ai/openai/azuresdk/ClientBase.java";

        String prompt = "Generate a Java Junit 5 test for the class:\n" + "\n" + "{{$input}}";

        CompletionSKFunction summarize =
                SKBuilders.completionFunctions()
                        .createFunction(
                                prompt,
                                "codeGen",
                                null,
                                null,
                                2000,
                                1,
                                0.5,
                                0,
                                0,
                                new ArrayList<>())
                        .registerOnKernel(kernel);

        String text =
                new String(
                        Files.readAllBytes(new File(fileName).toPath()), Charset.defaultCharset());

        Mono<CompletionSKContext> result = summarize.invokeAsync(text);

        LOGGER.info("Result: " + result.block().getResult());
    }
}
