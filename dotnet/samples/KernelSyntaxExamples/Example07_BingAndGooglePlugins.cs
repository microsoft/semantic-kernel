// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Plugins.Web;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
using Microsoft.SemanticKernel.Plugins.Web.Google;
using Xunit;
using Xunit.Abstractions;
using RepoUtils;

namespace Examples;

/// <summary>
/// The example shows how to use Bing and Google to search for current data
/// you might want to import into your system, e.g. providing AI prompts with
/// recent information, or for AI to generate recent information to display to users.
/// </summary>
public class Example07_BingAndGooglePlugins : BaseTest
{
    [Fact(Skip = "Setup Credentials")]
    public async Task RunAsync()
    {
        if (!ConfigurationValidator.Validate(nameof(Example07_BingAndGooglePlugins),
                new[] { TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey }, Output))
        {
            return;
        }

        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        // Load Bing plugin
        if (ConfigurationValidator.Validate(nameof(Example07_BingAndGooglePlugins),
                args: new[] { TestConfiguration.Bing.ApiKey }, output: Output, exampleNameSuffix: "Bing"))
        {
            var bingConnector = new BingConnector(TestConfiguration.Bing.ApiKey);
            var bing = new WebSearchEnginePlugin(bingConnector);
            kernel.ImportPluginFromObject(bing, "bing");
            await Example1Async(kernel, "bing");
            await Example2Async(kernel);
        }

        // Load Google plugin
        if (ConfigurationValidator.Validate(nameof(Example07_BingAndGooglePlugins),
                args: new[] { TestConfiguration.Google.ApiKey, TestConfiguration.Google.SearchEngineId }, output: Output, exampleNameSuffix: "Google"))
        {
            using var googleConnector = new GoogleConnector(
                apiKey: TestConfiguration.Google.ApiKey,
                searchEngineId: TestConfiguration.Google.SearchEngineId);
            kernel.ImportPluginFromObject(new WebSearchEnginePlugin(googleConnector), "google");
            // ReSharper disable once ArrangeThisQualifier
            await Example1Async(kernel, "google");
        }
    }

    private async Task Example1Async(Kernel kernel, string searchPluginName)
    {
        this.WriteLine("======== Bing and Google Search Plugins ========");

        // Run
        var question = "What's the largest building in the world?";
        var function = kernel.Plugins[searchPluginName]["search"];
        var result = await kernel.InvokeAsync(function, new() { ["query"] = question });

        this.WriteLine(question);
        this.WriteLine($"----{searchPluginName}----");
        this.WriteLine(result.GetValue<string>());

        /* OUTPUT:

            What's the largest building in the world?
            ----
            The Aerium near Berlin, Germany is the largest uninterrupted volume in the world, while Boeing's
            factory in Everett, Washington, United States is the world's largest building by volume. The AvtoVAZ
            main assembly building in Tolyatti, Russia is the largest building in area footprint.
            ----
            The Aerium near Berlin, Germany is the largest uninterrupted volume in the world, while Boeing's
            factory in Everett, Washington, United States is the world's ...
       */
    }

    private async Task Example2Async(Kernel kernel)
    {
        this.WriteLine("======== Use Search Plugin to answer user questions ========");

        const string SemanticFunction = @"Answer questions only when you know the facts or the information is provided.
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
{{ '{{' }} bing.search ""what\\'s Ferrari stock price?"" {{ '}}' }}.
{{ '{{' }} bing.search ""Who is the current number one female tennis player in the world?"" {{ '}}' }}.

[END OF EXAMPLES]

[TASK]
Question: {{ $question }}.
Answer: ";

        var question = "Who is the most followed person on TikTok right now? What's the exchange rate EUR:USD?";
        this.WriteLine(question);

        var oracle = kernel.CreateFunctionFromPrompt(SemanticFunction, new OpenAIPromptExecutionSettings() { MaxTokens = 150, Temperature = 0, TopP = 1 });

        var answer = await kernel.InvokeAsync(oracle, new KernelArguments()
        {
            ["question"] = question,
            ["externalInformation"] = string.Empty
        });

        var result = answer.GetValue<string>()!;

        // If the answer contains commands, execute them using the prompt renderer.
        if (result.Contains("bing.search", StringComparison.OrdinalIgnoreCase))
        {
            var promptTemplateFactory = new KernelPromptTemplateFactory();
            var promptTemplate = promptTemplateFactory.Create(new PromptTemplateConfig(result));

            this.WriteLine("---- Fetching information from Bing...");
            var information = await promptTemplate.RenderAsync(kernel);

            this.WriteLine("Information found:");
            this.WriteLine(information);

            // Run the prompt function again, now including information from Bing
            answer = await kernel.InvokeAsync(oracle, new KernelArguments()
            {
                ["question"] = question,
                // The rendered prompt contains the information retrieved from search engines
                ["externalInformation"] = information
            });
        }
        else
        {
            this.WriteLine("AI had all the information, no need to query Bing.");
        }

        this.WriteLine("---- ANSWER:");
        this.WriteLine(answer.GetValue<string>());

        /* OUTPUT:

            Who is the most followed person on TikTok right now? What's the exchange rate EUR:USD?
            ---- Fetching information from Bing...
            Information found:

            Khaby Lame is the most-followed user on TikTok. This list contains the top 50 accounts by number
            of followers on the Chinese social media platform TikTok, which was merged with musical.ly in 2018.
            [1] The most-followed individual on the platform is Khaby Lame, with over 153 million followers..
            EUR – Euro To USD – US Dollar 1.00 Euro = 1.10 37097 US Dollars 1 USD = 0.906035 EUR We use the
            mid-market rate for our Converter. This is for informational purposes only. You won’t receive this
            rate when sending money. Check send rates Convert Euro to US Dollar Convert US Dollar to Euro..
            ---- ANSWER:

            * The most followed person on TikTok right now is Khaby Lame, with over 153 million followers.
            * The exchange rate for EUR to USD is 1.1037097 US Dollars for 1 Euro.
         */
    }

    public Example07_BingAndGooglePlugins(ITestOutputHelper output) : base(output) { }
}
