// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.documentationexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.samples.plugins.MathPlugin;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionArguments;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;

public class UsingTheKernel {

    // CLIENT_KEY is for an OpenAI client
    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");

    // AZURE_CLIENT_KEY and CLIENT_ENDPOINT are for an Azure client
    // CLIENT_ENDPOINT required if AZURE_CLIENT_KEY is set
    private static final String AZURE_CLIENT_KEY = System.getenv("AZURE_CLIENT_KEY");
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");

    private static final String MODEL_ID = System.getenv()
        .getOrDefault("MODEL_ID", "gpt-3.5-turbo");

    public static void main(String[] args) {
        System.out.println("======== UsingTheKernel ========");

        OpenAIAsyncClient client;

        if (AZURE_CLIENT_KEY != null && CLIENT_ENDPOINT != null) {
            // <build_client>
            client = new OpenAIClientBuilder()
                .credential(new AzureKeyCredential(AZURE_CLIENT_KEY))
                .endpoint(CLIENT_ENDPOINT)
                .buildAsyncClient();
            // </build_client>
        } else if (CLIENT_KEY != null) {
            client = new OpenAIClientBuilder()
                .credential(new KeyCredential(CLIENT_KEY))
                .buildAsyncClient();
        } else {
            System.out.println("No client key found");
            return;
        }

        // <build_kernel>

        ChatCompletionService chatCompletionService = ChatCompletionService.builder()
            .withModelId(MODEL_ID)
            .withOpenAIAsyncClient(client)
            .build();

        KernelPlugin mathPlugin = KernelPluginFactory.createFromObject(
            new MathPlugin(), "MathPlugin");

        var poemPlugin = KernelPluginFactory.importPluginFromResourcesDirectory(
            "Plugins",
            "WriterPlugin",
            "ShortPoem",
            null,
            String.class);

        Kernel kernel = Kernel.builder()
            .withAIService(ChatCompletionService.class, chatCompletionService)
            .withPlugin(mathPlugin)
            .withPlugin(poemPlugin)
            .build();

        // </build_kernel>

        // <run_poem>
        var result = poemPlugin.get("ShortPoem")
            .invokeAsync(kernel)
            .withArguments(
                KernelFunctionArguments.builder()
                    .withInput("The cat sat on a mat")
                    .build())
            .withResultType(String.class)
            .block();
        System.out.println(result.getResult());
        // </run_poem>

        // <run_math>
        var root = mathPlugin.get("sqrt")
            .invokeAsync(kernel)
            .withArguments(
                KernelFunctionArguments.builder()
                    .withInput(12)
                    .build())
            .withResultType(Double.class)
            .block();
        System.out.println("Square root of 12 is: " + root.getResult());
        // </run_math>
    }
}
