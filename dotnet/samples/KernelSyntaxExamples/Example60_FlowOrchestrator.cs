// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Linq;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Experimental.Orchestration;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Plugins.Core;
using Microsoft.SemanticKernel.Plugins.Memory;
using Microsoft.SemanticKernel.Plugins.Web;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
using NCalcPlugins;

/**
 * This example shows how to use FlowOrchestrator to execute a given flow with interaction with client.
 */

// ReSharper disable once InconsistentNaming
public static class Example60_FlowOrchestrator
{
    private static readonly Flow s_flow = FlowSerializer.DeserializeFromYaml(@"
name: FlowOrchestrator_Example_Flow
goal: answer question and send email
steps:
  - goal: What is the tallest mountain on Earth? How tall is it divided by 2?
    plugins:
      - WebSearchEnginePlugin
      - LanguageCalculatorPlugin
    provides:
      - answer
  - goal: Collect email address
    plugins:
      - ChatPlugin
    completionType: AtLeastOnce
    transitionMessage: do you want to send it to another email address?
    provides:
      - email_addresses

  - goal: Send email
    plugins:
      - EmailPluginV2
    requires:
      - email_addresses
      - answer
    provides:
      - email

provides:
    - email
");

    public static Task RunAsync()
    {
        // Load assemblies for external plugins
        Console.WriteLine("Loading {0}", typeof(SimpleCalculatorPlugin).AssemblyQualifiedName);

        return RunExampleAsync();
        //return RunInteractiveAsync();
    }

    private static async Task RunInteractiveAsync()
    {
        var bingConnector = new BingConnector(TestConfiguration.Bing.ApiKey);
        var webSearchEnginePlugin = new WebSearchEnginePlugin(bingConnector);
        using var loggerFactory = LoggerFactory.Create(loggerBuilder =>
            loggerBuilder
                .AddConsole()
                .AddFilter(null, LogLevel.Warning));
        Dictionary<object, string?> plugins = new()
        {
            { webSearchEnginePlugin, "WebSearch" },
            { new TimePlugin(), "time" }
        };

        FlowOrchestrator orchestrator = new(
            GetKernelBuilder(loggerFactory),
            await FlowStatusProvider.ConnectAsync(new VolatileMemoryStore()).ConfigureAwait(false),
            plugins,
            config: GetOrchestratorConfig());
        var sessionId = Guid.NewGuid().ToString();

        Console.WriteLine("*****************************************************");
        Stopwatch sw = new();
        sw.Start();
        Console.WriteLine("Flow: " + s_flow.Name);
        ContextVariables? result = null;
        string? input = null;// "Execute the flow";// can this be empty?
        do
        {
            if (result is not null)
            {
                Console.WriteLine("Assistant: " + result.ToString());
            }

            if (string.IsNullOrEmpty(input))
            {
                Console.WriteLine("User: ");
                input = Console.ReadLine() ?? string.Empty;
                s_flow.Steps.First().Goal = input;
            }

            result = await orchestrator.ExecuteFlowAsync(s_flow, sessionId, input); // This should change to be a FunctionResult or KernelResult probably
        } while (!string.IsNullOrEmpty(result.ToString()) && result.ToString() != "[]");

        Console.WriteLine("Assistant: " + result["answer"]);

        Console.WriteLine("Time Taken: " + sw.Elapsed);
        Console.WriteLine("*****************************************************");
    }

    private static async Task RunExampleAsync()
    {
        var bingConnector = new BingConnector(TestConfiguration.Bing.ApiKey);
        var webSearchEnginePlugin = new WebSearchEnginePlugin(bingConnector);
        using var loggerFactory = LoggerFactory.Create(loggerBuilder =>
            loggerBuilder
                .AddConsole()
                .AddFilter(null, LogLevel.Error));

        Dictionary<object, string?> plugins = new()
        {
            { webSearchEnginePlugin, "WebSearch" },
            { new TimePlugin(), "time" }
        };

        FlowOrchestrator orchestrator = new(
            GetKernelBuilder(loggerFactory),
            await FlowStatusProvider.ConnectAsync(new VolatileMemoryStore()).ConfigureAwait(false),
            plugins,
            config: GetOrchestratorConfig());
        var sessionId = Guid.NewGuid().ToString();

        Console.WriteLine("*****************************************************");
        Stopwatch sw = new();
        sw.Start();
        Console.WriteLine("Flow: " + s_flow.Name);
        var result = await orchestrator.ExecuteFlowAsync(s_flow, sessionId, "Execute the flow").ConfigureAwait(false);

        Console.WriteLine("Question: " + s_flow.Steps.First().Goal);
        Console.WriteLine("Answer: " + result["answer"]);
        Console.WriteLine("Assistant: " + result.ToString());

        string[] userInputs = new[]
        {
            "my email is bad*email&address",
            "my email is sample@xyz.com",
            "yes", // confirm to add another email address
            "I also want to notify foo@bar.com",
            "no I don't need notify any more address", // end of collect emails
        };

        foreach (var t in userInputs)
        {
            Console.WriteLine($"User: {t}");
            result = await orchestrator.ExecuteFlowAsync(s_flow, sessionId, t).ConfigureAwait(false);
            Console.WriteLine("Assistant: " + result.ToString());

            if (result.IsComplete(s_flow))
            {
                break;
            }
        }

        Console.WriteLine("\tEmail Address: " + result["email_addresses"]);
        Console.WriteLine("\tEmail Payload: " + result["email"]);

        Console.WriteLine("Time Taken: " + sw.Elapsed);
        Console.WriteLine("*****************************************************");
    }

    private static FlowOrchestratorConfig GetOrchestratorConfig()
    {
        var config = new FlowOrchestratorConfig();
        config.ExcludedFunctions.Add("DaysAgo");
        config.ExcludedFunctions.Add("DateMatchingLastDayName");
        config.ReActModel = FlowOrchestratorConfig.ModelName.GPT35_TURBO;
        config.MaxStepIterations = 20;

        return config;
    }

    private static KernelBuilder GetKernelBuilder(ILoggerFactory loggerFactory)
    {
        var builder = new KernelBuilder();

        return builder
            .WithAzureChatCompletionService(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey,
                true,
                setAsDefault: true)
            .WithRetryBasic(new()
            {
                MaxRetryCount = 3,
                UseExponentialBackoff = true,
                MinRetryDelay = TimeSpan.FromSeconds(3),
            })
            .WithLoggerFactory(loggerFactory);
    }

    public sealed class ChatPlugin
    {
        private const string Goal = "Prompt user to provide a valid email address";

        private const string EmailRegex = @"^([\w\.\-]+)@([\w\-]+)((\.(\w){2,3})+)$";

        private const string SystemPrompt =
            $@"I am AI assistant and will only answer questions related to collect email.
The email should conform the regex: {EmailRegex}

If I cannot answer, say that I don't know.
Do not expose the regex unless asked.
";

        private readonly IChatCompletion _chat;

        private int MaxTokens { get; set; } = 256;

        private readonly AIRequestSettings _chatRequestSettings;

        public ChatPlugin(IKernel kernel)
        {
            this._chat = kernel.GetService<IChatCompletion>();
            this._chatRequestSettings = new OpenAIRequestSettings
            {
                MaxTokens = this.MaxTokens,
                StopSequences = new List<string>() { "Observation:" },
                Temperature = 0
            };
        }

        [SKFunction]
        [Description("Useful to assist in configuration of email address, must be called after email provided")]
        [SKName("ConfigureEmailAddress")]
        public async Task<string> CollectEmailAsync(
            [SKName("email_address")]
            [Description("The email address provided by the user, pass no matter what the value is")]
            string email,
            SKContext context)
        {
            var chat = this._chat.CreateNewChat(SystemPrompt);
            chat.AddUserMessage(Goal);

            ChatHistory? chatHistory = context.GetChatHistory();
            if (chatHistory?.Any() ?? false)
            {
                chat.Messages.AddRange(chatHistory);
            }

            if (!string.IsNullOrEmpty(email) && IsValidEmail(email))
            {
                context.Variables["email_addresses"] = email;

                return "Thanks for providing the info, the following email would be used in subsequent steps: " + email;
            }

            context.Variables["email_addresses"] = string.Empty;
            context.PromptInput();

            return await this._chat.GenerateMessageAsync(chat, this._chatRequestSettings).ConfigureAwait(false);
        }

        private static bool IsValidEmail(string email)
        {
            // check using regex
            var regex = new Regex(EmailRegex);
            return regex.IsMatch(email);
        }
    }

    public sealed class EmailPluginV2
    {
        [SKFunction]
        [Description("Send email")]
        [SKName("SendEmail")]
        public string SendEmail(
            [SKName("email_addresses")][Description("target email addresses")]
            string emailAddress,
            [SKName("answer")][Description("answer, which is going to be the email content")]
            string answer,
            SKContext context)
        {
            var contract = new Email()
            {
                Address = emailAddress,
                Content = answer,
            };

            // for demo purpose only
            string emailPayload = JsonSerializer.Serialize(contract, new JsonSerializerOptions() { WriteIndented = true });
            context.Variables["email"] = emailPayload;

            return "Here's the API contract I will post to mail server: " + emailPayload;
        }

        private sealed class Email
        {
            public string? Address { get; set; }

            public string? Content { get; set; }
        }
    }
}
//*****************************************************
//Flow: FlowOrchestrator_Example_Flow
//Question: What is the tallest mountain on Earth? How tall is it divided by 2?
//Answer: The tallest mountain on Earth is Mount Everest, which has a height of 29,031.69 feet (8,848.86 meters) above sea level. Half of its height is 14,515.845 feet (4,424.43 meters).
//Assistant: ["Please provide a valid email address."]
//User: my email is bad*email&address
//Assistant: ["I\u0027m sorry, but \u0022bad*email\u0026address\u0022 is not a valid email address. A valid email address should have the format \u0022example@example.com\u0022."]
//User: my email is sample@xyz.com
//Assistant: ["Do you want to send it to another email address?"]
//User: yes
//Assistant: ["Please provide a valid email address."]
//User: I also want to notify foo@bar.com
//Assistant: ["Do you want to send it to another email address?"]
//User: no I don't need notify any more address
//Assistant: []
//        Email Address: ["sample@xyz.com","foo@bar.com"]
//        Email Payload: {
//  "Address": "[\u0022sample@xyz.com\u0022,\u0022foo@bar.com\u0022]",
//  "Content": "The tallest mountain on Earth is Mount Everest, which has a height of 29,031.69 feet (8,848.86 meters) above sea level. Half of its height is 14,515.845 feet (4,424.43 meters)."
//}
//Time Taken: 00:00:22.7646223
//*****************************************************
