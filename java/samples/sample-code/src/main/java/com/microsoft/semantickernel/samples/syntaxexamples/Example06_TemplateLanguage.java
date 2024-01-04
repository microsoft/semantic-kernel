package com.microsoft.semantickernel.samples.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.DefaultKernel;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.azureopenai.AzureOpenAITextGenerationService;
import com.microsoft.semantickernel.exceptions.ConfigurationException;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings.Builder;
import com.microsoft.semantickernel.plugin.KernelFunctionFactory;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.plugin.annotations.DefineKernelFunction;
import com.microsoft.semantickernel.semanticfunctions.KernelPromptTemplateFactory;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.textcompletion.TextGenerationService;

public class Example06_TemplateLanguage {


    public static class Time {

        @DefineKernelFunction(name = "date")
        public String date() {
            return "2021-09-01";
        }

        @DefineKernelFunction(name = "time")
        public String time() {
            return "12:00:00";
        }
    }

    public static void main(String[] args) throws ConfigurationException {

        System.out.println("======== TemplateLanguage ========");

        TextGenerationService textGenerationService;

        String clientKey = System.getenv("CLIENT_KEY");

        if (Boolean.parseBoolean(System.getenv("USE_AZURE_CLIENT"))) {
            String clientEndpoint = System.getenv("CLIENT_ENDPOINT");

            OpenAIAsyncClient client = new OpenAIClientBuilder()
                .credential(new AzureKeyCredential(clientKey))
                .endpoint(clientEndpoint)
                .buildAsyncClient();

            textGenerationService = AzureOpenAITextGenerationService.builder()
                .withOpenAIAsyncClient(client)
                .withModelId("text-davinci-003")
                .build();
        } else {
            OpenAIAsyncClient client = new OpenAIClientBuilder()
                .credential(new KeyCredential(clientKey))
                .buildAsyncClient();

            // TODO: Add support for OpenAI API
            textGenerationService = null;
        }

        Kernel kernel = new DefaultKernel.Builder()
            .withDefaultAIService(TextGenerationService.class, textGenerationService)
            .build();

        // Load native plugin into the kernel function collection, sharing its functions with prompt templates
        // Functions loaded here are available as "time.*"
        KernelPlugin time = KernelPluginFactory.createFromObject(
            new Time(), "time");

        kernel.getPlugins().add(time);

        // Prompt Function invoking time.Date and time.Time method functions
        String functionDefinition = """
            Today is: {{time.date}}
            Current time is: {{time.time}}

            Answer to the following questions using JSON syntax, including the data used.
                Is it morning, afternoon, evening, or night (morning/afternoon/evening/night)?
                Is it weekend time (weekend/not weekend)?
                """;

        // This allows to see the prompt before it's sent to OpenAI
        System.out.println("--- Rendered Prompt");

        var promptTemplateFactory = new KernelPromptTemplateFactory();

        var promptTemplate = promptTemplateFactory.tryCreate(
            new PromptTemplateConfig(functionDefinition));

        var renderedPrompt = promptTemplate.renderAsync(kernel, null).block();
        System.out.println(renderedPrompt);

        var kindOfDay = KernelFunctionFactory
            .createFromPrompt(
                functionDefinition,
                new Builder()
                    .withMaxTokens(100)
                    .build(),
                null,
                null,
                "semantic-kernel",
                null);

        // Show the result
        System.out.println("--- Prompt Function result");
        var result = kernel.invokeAsync(kindOfDay, null, String.class).block();
        System.out.println(result.getValue());
    }
}
