// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.syntaxexamples.java;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.Kernel.Builder;
import com.microsoft.semantickernel.exceptions.ConfigurationException;
import com.microsoft.semantickernel.implementation.EmbeddedResourceLoader;
import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.semanticfunctions.KernelFunction;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionArguments;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionYaml;
import com.microsoft.semantickernel.services.textcompletion.TextGenerationService;
import java.io.IOException;

public class KernelFunctionYaml_Example {

    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");
    private static final String AZURE_CLIENT_KEY = System.getenv("AZURE_CLIENT_KEY");

    // Only required if AZURE_CLIENT_KEY is set
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");
    private static final String MODEL_ID = System.getenv()
        .getOrDefault("MODEL_ID", "text-davinci-003");

    public static void main(String[] args) throws ConfigurationException, IOException {

        OpenAIAsyncClient client;

        if (AZURE_CLIENT_KEY != null) {
            client = new OpenAIClientBuilder()
                .credential(new AzureKeyCredential(AZURE_CLIENT_KEY))
                .endpoint(CLIENT_ENDPOINT)
                .buildAsyncClient();
        } else {
            client = new OpenAIClientBuilder()
                .credential(new KeyCredential(CLIENT_KEY))
                .buildAsyncClient();
        }

        TextGenerationService textGenerationService = TextGenerationService.builder()
            .withOpenAIAsyncClient(client)
            .withModelId(MODEL_ID)
            .build();

        Builder kernelBuilder = Kernel.builder()
            .withAIService(TextGenerationService.class, textGenerationService);

        semanticKernelTemplate(kernelBuilder.build());
        handlebarsTemplate(kernelBuilder.build());

    }

    private static void handlebarsTemplate(Kernel kernel) throws IOException {
        String yaml = EmbeddedResourceLoader.readFile("GenerateStoryHandlebars.yaml",
            KernelFunctionYaml_Example.class);

        KernelFunction<String> function = KernelFunctionYaml.fromPromptYaml(yaml);

        FunctionResult<String> result = function
            .invokeAsync(kernel)
            .withArguments(
                KernelFunctionArguments.builder()
                    .withVariable("length", 5)
                    .withVariable("topic", "dogs")
                    .build())
            .block();

        System.out.println(result.getResult());
    }

    private static void semanticKernelTemplate(Kernel kernel) throws IOException {
        String yaml = EmbeddedResourceLoader.readFile("GenerateStory.yaml",
            KernelFunctionYaml_Example.class);

        KernelFunction<String> function = KernelFunctionYaml.fromPromptYaml(yaml);

        FunctionResult<String> result = function
            .invokeAsync(kernel)
            .withArguments(
                KernelFunctionArguments.builder()
                    .withVariable("length", 5)
                    .withVariable("topic", "cats")
                    .build())
            .block();

        System.out.println(result.getResult());
    }

}
