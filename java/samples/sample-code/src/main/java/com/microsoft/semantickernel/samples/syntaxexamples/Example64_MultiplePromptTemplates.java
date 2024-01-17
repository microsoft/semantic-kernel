package com.microsoft.semantickernel.samples.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.DefaultKernel;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.openai.chatcompletion.OpenAIChatCompletion;
import com.microsoft.semantickernel.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import com.microsoft.semantickernel.semanticfunctions.AggregatorPromptTemplateFactory;
import com.microsoft.semantickernel.semanticfunctions.HandlebarsPromptTemplateFactory;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromPrompt;
import com.microsoft.semantickernel.semanticfunctions.KernelPromptTemplateFactory;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateFactory;

import java.util.List;

public class Example64_MultiplePromptTemplates {

    private static final boolean USE_AZURE_CLIENT = Boolean.parseBoolean(
            System.getenv("USE_AZURE_CLIENT"));
    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");

    // Only required if USE_AZURE_CLIENT is true
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");

    public static void main(String[] args) {
        System.out.println("======== Example64_MultiplePromptTemplates ========");

        OpenAIAsyncClient client;

        if (USE_AZURE_CLIENT) {
            client = new OpenAIClientBuilder()
                    .credential(new AzureKeyCredential(CLIENT_KEY))
                    .endpoint(CLIENT_ENDPOINT)
                    .buildAsyncClient();
        } else {
            client = new OpenAIClientBuilder()
                    .credential(new KeyCredential(CLIENT_KEY))
                    .buildAsyncClient();
        }

        ChatCompletionService chatCompletion = OpenAIChatCompletion.builder()
                .withModelId("gpt-35-turbo")
                .withOpenAIAsyncClient(client)
                .build();

        var kernel = new DefaultKernel.Builder()
                .withDefaultAIService(ChatCompletionService.class, chatCompletion)
                .build();

        var templateFactory = new AggregatorPromptTemplateFactory(
                List.of(
                        new KernelPromptTemplateFactory(),
                        new HandlebarsPromptTemplateFactory()
                )
        );

        runPrompt(kernel,
                "semantic-kernel",
                "Hello AI, my name is {{$name}}. What is the origin of my name?",
                templateFactory);
        runPrompt(kernel,
                "handlebars",
                "Hello AI, my name is {{name}}. What is the origin of my name?",
                templateFactory);
    }

    public static void runPrompt (Kernel kernel, String templateFormat, String prompt, PromptTemplateFactory templateFactory) {
        var function = new KernelFunctionFromPrompt.Builder()
                .withTemplate(prompt)
                .withTemplateFormat(templateFormat)
                .withPromptTemplateFactory(templateFactory)
                .build();

        var arguments = KernelArguments.builder()
                .withVariable("name", "Bob")
                .build();

        var result = kernel.invokeAsync(function, arguments, String.class).block();
        System.out.println(result.getValue());
    }
}
