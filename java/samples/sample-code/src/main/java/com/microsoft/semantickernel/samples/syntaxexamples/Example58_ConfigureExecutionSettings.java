// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.openai.chatcompletion.OpenAIChatCompletion;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.semanticfunctions.KernelFunction;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromPrompt;
import com.microsoft.semantickernel.semanticfunctions.OutputVariable;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;

public class Example58_ConfigureExecutionSettings {

    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");
    private static final String AZURE_CLIENT_KEY = System.getenv("AZURE_CLIENT_KEY");

    // Only required if AZURE_CLIENT_KEY is set
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");
    private static final String MODEL_ID = System.getenv()
        .getOrDefault("MODEL_ID", "gpt-35-turbo");

    public static void main(String[] args) {
        System.out.println("======== Example58_ConfigureExecutionSettings ========");

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

        ChatCompletionService openAIChatCompletion = OpenAIChatCompletion.builder()
            .withModelId(MODEL_ID)
            .withOpenAIAsyncClient(client)
            .build();

        var kernel = Kernel.builder()
            .withAIService(ChatCompletionService.class, openAIChatCompletion)
            .build();

        var prompt = "Hello AI, what can you do for me?";

        // Option 1:
        // Invoke the prompt function and pass an OpenAI specific instance containing the execution settings
        var result = kernel.invokeAsync(
            KernelFunctionFromPrompt.builder()
                .withTemplate(prompt)
                .withDefaultExecutionSettings(
                    PromptExecutionSettings.builder()
                        .withMaxTokens(60)
                        .withTemperature(0.7)
                        .build())
                .withOutputVariable(new OutputVariable("java.lang.String", "result"))
                .build())
            .block();

        System.out.println(result.getResult());

        // Option 2:
        // Load prompt template configuration including the execution settings from a JSON payload
        // Create the prompt functions using the prompt template and the configuration (loaded in the previous step)
        // Invoke the prompt function using the implicitly set execution settings
        String configPayload = """
              {
              "schema": 1,
              "name": "HelloAI",
              "description": "Say hello to an AI",
              "type": "completion",
              "completion": {
                "max_tokens": 256,
                "temperature": 0.5,
                "top_p": 0.0,
                "presence_penalty": 0.0,
                "frequency_penalty": 0.0
              }
            }""".stripIndent();

        var promptConfig = PromptTemplateConfig
            .parseFromJson(configPayload)
            .copy()
            .withTemplate(prompt)
            .build();

        var func = KernelFunction
            .createFromPrompt(promptConfig)
            .build();

        result = kernel.invokeAsync(func).block();
        System.out.println(result.getResult());
    }
}
