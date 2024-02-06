package com.microsoft.semantickernel.samples.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.openai.chatcompletion.OpenAIChatCompletion;
import com.microsoft.semantickernel.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.orchestration.KernelFunctionArguments;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.plugins.text.TextPlugin;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromPrompt;
import com.microsoft.semantickernel.semanticfunctions.KernelPromptTemplateFactory;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;

public class Example56_TemplateMethodFunctionsWithMultipleArguments {

    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");
    private static final String AZURE_CLIENT_KEY = System.getenv("AZURE_CLIENT_KEY");

    // Only required if AZURE_CLIENT_KEY is set
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");
    private static final String MODEL_ID = System.getenv()
        .getOrDefault("MODEL_ID", "gpt-35-turbo");

    public static void main(String[] args) {

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

        Kernel kernel = Kernel.builder()
            .withAIService(ChatCompletionService.class, openAIChatCompletion)
            .build();

        System.out.println("======== TemplateMethodFunctionsWithMultipleArguments ========");

        var arguments = KernelFunctionArguments.builder()
            .withVariable("word2", " Potter")
            .build();

        // Load native plugin into the kernel function collection, sharing its functions with prompt templates
        // Functions loaded here are available as "text.*"
        kernel.getPlugins().add(KernelPluginFactory.createFromObject(new TextPlugin(), "text"));

        // Prompt Function invoking text.Concat method function with named arguments input and input2 where input is a string and input2 is set to a variable from context called word2.
        String functionDefinition = "Write a haiku about the following: {{text.Concat input='Harry' input2=$word2}}";

        // This allows to see the prompt before it's sent to OpenAI
        System.out.println("--- Rendered Prompt");
        var promptTemplateFactory = new KernelPromptTemplateFactory();
        var promptTemplate = promptTemplateFactory.tryCreate(
            new PromptTemplateConfig(functionDefinition));
        var renderedPrompt = promptTemplate.renderAsync(kernel, arguments).block();
        System.out.println(renderedPrompt);

        // Run the prompt / prompt function

        var haiku = KernelFunctionFromPrompt
            .builder()
            .withTemplate(functionDefinition)
            .withDefaultExecutionSettings(
                PromptExecutionSettings.builder()
                    .withMaxTokens(100)
                    .build())
            .build();

        // Show the result
        System.out.println("--- Prompt Function result");
        var result = kernel.invokeAsync(haiku).withArguments(arguments).block();
        System.out.println(result.getResult());
    }

}
