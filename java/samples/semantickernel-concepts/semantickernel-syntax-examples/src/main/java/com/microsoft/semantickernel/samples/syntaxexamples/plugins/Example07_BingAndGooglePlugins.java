// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.syntaxexamples.plugins;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.openai.chatcompletion.OpenAIChatCompletion;
import com.microsoft.semantickernel.samples.connectors.web.bing.BingConnector;
import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.samples.plugins.web.WebSearchEnginePlugin;
import com.microsoft.semantickernel.semanticfunctions.KernelFunction;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionArguments;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromPrompt;
import com.microsoft.semantickernel.semanticfunctions.KernelPromptTemplateFactory;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;

/// <summary>
/// The example shows how to use Bing and Google to search for current data
/// you might want to import into your system, e.g. providing AI prompts with
/// recent information, or for AI to generate recent information to display to users.
/// </summary>
public class Example07_BingAndGooglePlugins {

    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");
    private static final String AZURE_CLIENT_KEY = System.getenv("AZURE_CLIENT_KEY");

    // Only required if AZURE_CLIENT_KEY is set
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");
    private static final String MODEL_ID = System.getenv()
        .getOrDefault("MODEL_ID", "gpt-3.5-turbo");

    private static final String BING_API_KEY = System.getenv("BING_API_KEY");
    private static final String GOOGLE_API_KEY = System.getenv("GOOGLE_API_KEY");
    private static final String GOOGLE_SEARCH_ENGINE_ID = System.getenv("GOOGLE_SEARCH_ENGINE_ID");

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

        // Load Bing plugin
        var bingConnector = new BingConnector(BING_API_KEY);
        var bing = KernelPluginFactory.createFromObject(new WebSearchEnginePlugin(bingConnector),
            "bing");

        var chatCompletionService = OpenAIChatCompletion.builder()
            .withOpenAIAsyncClient(client)
            .withModelId(MODEL_ID)
            .build();

        var kernel = Kernel.builder()
            .withPlugin(bing)
            .withAIService(ChatCompletionService.class, chatCompletionService)
            .build();

        example1Async(kernel, "bing");
        example2Async(kernel);

        // Load Google plugin
        // WebSearchEngineConnector googleConnector = new GoogleConnector(GOOGLE_API_KEY, GOOGLE_SEARCH_ENGINE_ID);
        // WebSearchEnginePlugin bing = new WebSearchEnginePlugin(googleConnector);
        // kernel.importPluginFromObject(new WebSearchEnginePlugin(googleConnector), "google");
    }

    private static void example1Async(Kernel kernel, String searchPluginName) {
        System.out.println("======== Bing and Google Search Plugins ========");

        // Run
        var question = "What's the largest building in the world?";
        var kernelArguments = KernelFunctionArguments.builder()
            .withVariable("query", question)
            .build();

        var function = kernel.getFunction(searchPluginName, "search");
        var result = kernel.invokeAsync(function).withArguments(kernelArguments).block();

        System.out.println(question);
        System.out.printf("----%s----%n", searchPluginName);
        System.out.println(result.getResult());

        /*
         * OUTPUT:
         *
         * What's the largest building in the world?
         * ----
         * The Aerium near Berlin, Germany is the largest uninterrupted volume in the world, while
         * Boeing's
         * factory in Everett, Washington, United States is the world's largest building by volume.
         * The AvtoVAZ
         * main assembly building in Tolyatti, Russia is the largest building in area footprint.
         * ----
         * The Aerium near Berlin, Germany is the largest uninterrupted volume in the world, while
         * Boeing's
         * factory in Everett, Washington, United States is the world's ...
         */
    }

    private static void example2Async(Kernel kernel) {
        System.out.println("======== Use Search Plugin to answer user questions ========");

        var semanticFunction = """
                Answer questions only when you know the facts or the information is provided.
                When you don't have sufficient information you reply with a list of commands to find the information needed.
                When answering multiple questions, use a bullet point list.
                Note: make sure single and double quotes are escaped using a backslash char.

                [COMMANDS AVAILABLE]
                - bing.search

                [INFORMATION PROVIDED]
                {{ $externalInformation }}

                [EXAMPLE 1]
                Question: what's the biggest lake in Italy?
                Answer: Lake Garda, also known as Lago di Garda.

                [EXAMPLE 2]
                Question: what's the biggest lake in Italy? What's the smallest positive number?
                Answer:
                * Lake Garda, also known as Lago di Garda.
                * The smallest positive number is 1.

                [EXAMPLE 3]
                Question: what's Ferrari stock price? Who is the current number one female tennis player in the world?
                Answer:
                {{ '{{' }} bing.search "what's Ferrari stock price?" {{ '}}' }}.
                {{ '{{' }} bing.search "Who is the current number one female tennis player in the world?" {{ '}}' }}.

                [END OF EXAMPLES]

                [TASK]
                Question: {{ $question }}.
                Answer:
            """
            .stripIndent();

        // The prompt function will append the answer here
        var question = "Who is the most followed person on TikTok right now? What's the exchange rate EUR:USD?";
        System.out.println(question);

        var promptExecutionSettings = PromptExecutionSettings.builder()
            .withMaxTokens(150)
            .withTemperature(0)
            .withTopP(1)
            .build();

        KernelFunction<String> oracle = KernelFunctionFromPrompt.<String>builder()
            .withTemplate(semanticFunction)
            .withDefaultExecutionSettings(promptExecutionSettings)
            .build();

        var kernelArguments = KernelFunctionArguments.builder()
            .withVariable("question", question)
            .withVariable("externalInformation", "")
            .build();

        FunctionResult<String> answer = kernel.invokeAsync(oracle).withArguments(kernelArguments)
            .block();

        var result = answer.getResult();

        // If the answer contains commands, execute them using the prompt renderer.
        if (result.contains("bing.search")) {
            PromptTemplate promptTemplate = new KernelPromptTemplateFactory()
                .tryCreate(PromptTemplateConfig.builder().withTemplate(result).build());

            System.out.println("---- Fetching information from Bing...");
            var information = promptTemplate.renderAsync(kernel, null, null).block();

            System.out.println("Information found:");
            System.out.println(information);

            kernelArguments = KernelFunctionArguments.builder()
                .withVariable("question", question)
                .withVariable("externalInformation", information)
                .build();

            // Run the prompt function again, now including information from Bing
            answer = kernel.invokeAsync(oracle).withArguments(kernelArguments).block();
        } else {
            System.out.println("AI had all the information, no need to query Bing.");
        }

        System.out.println("---- ANSWER:");
        System.out.println(answer.getResult());

        /*
         * OUTPUT:
         *
         * Who is the most followed person on TikTok right now? What's the exchange rate EUR:USD?
         * ---- Fetching information from Bing...
         * Information found:
         *
         * Khaby Lame is the most-followed user on TikTok. This list contains the top 50 accounts by
         * number
         * of followers on the Chinese social media platform TikTok, which was merged with
         * musical.ly in 2018.
         * [1] The most-followed individual on the platform is Khaby Lame, with over 153 million
         * followers..
         * EUR – Euro To USD – US Dollar 1.00 Euro = 1.10 37097 US Dollars 1 USD = 0.906035 EUR We
         * use the
         * mid-market rate for our Converter. This is for informational purposes only. You won’t
         * receive this
         * rate when sending money. Check send rates Convert Euro to US Dollar Convert US Dollar to
         * Euro..
         * ---- ANSWER:
         *
         * The most followed person on TikTok right now is Khaby Lame, with over 153 million
         * followers.
         * The exchange rate for EUR to USD is 1.1037097 US Dollars for 1 Euro.
         */
    }

}
