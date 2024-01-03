package com.microsoft.semantickernel.samples.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.DefaultKernel;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.azureopenai.AzureOpenAITextGenerationService;
import com.microsoft.semantickernel.exceptions.ConfigurationException;
import com.microsoft.semantickernel.samples.SamplesConfig;
import com.microsoft.semantickernel.textcompletion.TextGenerationService;

public class Example06_TemplateLanguage {

    public static void main(String[] args) throws ConfigurationException {

        System.out.println("======== TemplateLanguage ========");

        OpenAIAsyncClient client = SamplesConfig.getClient();

        AzureOpenAITextGenerationService textGenerationService = AzureOpenAITextGenerationService.builder()
            .withOpenAIAsyncClient(client)
            .withModelId("text-davinci-003")
            .build();

        Kernel kernel = new DefaultKernel.Builder()
            .withDefaultAIService(TextGenerationService.class, textGenerationService)
            .build();
/*
        // Load native plugin into the kernel function collection, sharing its functions with prompt templates
        // Functions loaded here are available as "time.*"
        kernel.importPluginFromType("time");

        // Prompt Function invoking time.Date and time.Time method functions
        String functionDefinition = """
            Today is: {{time.Date}}
            Current time is: {{time.Time}}

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

        // Run the prompt / prompt function
        var kindOfDay = kernel
            .createFunctionFromPrompt(
                functionDefinition,
                new PromptExecutionSettings.Builder()
                    .withMaxTokens(100)
                    .build(),
                null,
                null,
                null,
                null);

        // Show the result
        System.out.println("--- Prompt Function result");
        var result = kernel.invokeAsync(kindOfDay, null);
        System.out.println(result.GetValue < string > ());
*/
    }
}
