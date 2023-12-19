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
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Experimental.Orchestration;
using Microsoft.SemanticKernel.Plugins.Core;
using Microsoft.SemanticKernel.Plugins.Memory;
using Microsoft.SemanticKernel.Plugins.Web;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
using NCalcPlugins;

/**
 * This example shows how to use FlowOrchestrator to execute a given flow with interaction with client.
 */
// ReSharper disable once InconsistentNaming
public static class Example63_FlowOrchestrator
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
                .AddFilter(null, LogLevel.Error));
        Dictionary<object, string?> plugins = new()
        {
            { webSearchEnginePlugin, "WebSearch" },
            { new TimePlugin(), "Time" }
        };

        FlowOrchestrator orchestrator = new(
            GetKernelBuilder(loggerFactory),
            await FlowStatusProvider.ConnectAsync(new VolatileMemoryStore()).ConfigureAwait(false),
            plugins,
            config: GetOrchestratorConfig());
        var sessionId = Guid.NewGuid().ToString();

        Console.WriteLine("*****************************************************");
        Console.WriteLine("Executing {0}", nameof(RunInteractiveAsync));
        Stopwatch sw = new();
        sw.Start();
        Console.WriteLine("Flow: " + s_flow.Name);
        Console.WriteLine("Please type the question you'd like to ask");
        ContextVariables? result;
        string? goal = null;
        do
        {
            Console.WriteLine("User: ");
            string input = Console.ReadLine() ?? string.Empty;

            if (string.IsNullOrEmpty(input))
            {
                Console.WriteLine("No input, exiting");
                break;
            }

            if (string.IsNullOrEmpty(goal))
            {
                s_flow.Steps.First().Goal = input;
            }

            result = await orchestrator.ExecuteFlowAsync(s_flow, sessionId, input);
            Console.WriteLine("Assistant: " + result.ToString());

            if (result.IsComplete(s_flow))
            {
                Console.WriteLine("\tEmail Address: " + result["email_addresses"]);
                Console.WriteLine("\tEmail Payload: " + result["email"]);

                Console.WriteLine("Flow completed, exiting");
                break;
            }
        } while (!string.IsNullOrEmpty(result.ToString()) && result.ToString() != "[]");

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
            { new TimePlugin(), "Time" }
        };

        FlowOrchestrator orchestrator = new(
            GetKernelBuilder(loggerFactory),
            await FlowStatusProvider.ConnectAsync(new VolatileMemoryStore()).ConfigureAwait(false),
            plugins,
            config: GetOrchestratorConfig());
        var sessionId = Guid.NewGuid().ToString();

        Console.WriteLine("*****************************************************");
        Console.WriteLine("Executing {0}", nameof(RunExampleAsync));
        Stopwatch sw = new();
        sw.Start();
        Console.WriteLine("Flow: " + s_flow.Name);
        var question = s_flow.Steps.First().Goal;
        var result = await orchestrator.ExecuteFlowAsync(s_flow, sessionId, question).ConfigureAwait(false);

        Console.WriteLine("Question: " + question);
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
        var config = new FlowOrchestratorConfig
        {
            MaxStepIterations = 20
        };

        return config;
    }

    private static KernelBuilder GetKernelBuilder(ILoggerFactory loggerFactory)
    {
        var builder = Kernel.CreateBuilder();

        return builder
            .WithAzureOpenAIChatCompletion(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey)
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

        private readonly PromptExecutionSettings _chatRequestSettings;

        public ChatPlugin(Kernel kernel)
        {
            this._chat = kernel.GetService<IChatCompletion>();
            this._chatRequestSettings = new OpenAIPromptExecutionSettings
            {
                MaxTokens = this.MaxTokens,
                StopSequences = new List<string>() { "Observation:" },
                Temperature = 0
            };
        }

        [KernelFunction("ConfigureEmailAddress")]
        [Description("Useful to assist in configuration of email address, must be called after email provided")]
        public async Task<string> CollectEmailAsync(
            [Description("The email address provided by the user, pass no matter what the value is")]
            string email_address,
            ContextVariables variables)
        {
            var chat = this._chat.CreateNewChat(SystemPrompt);
            chat.AddUserMessage(Goal);

            ChatHistory? chatHistory = variables.GetChatHistory();
            if (chatHistory?.Any() ?? false)
            {
                chat.AddRange(chatHistory);
            }

            if (!string.IsNullOrEmpty(email) && IsValidEmail(email))
            {
                variables["email_addresses"] = email;

                return "Thanks for providing the info, the following email would be used in subsequent steps: " + email;
            }

            variables["email_addresses"] = string.Empty;
            variables.PromptInput();

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
        [KernelFunction]
        [Description("Send email")]
        public string SendEmail(
            [Description("target email addresses")]
            string email_addresses,
            [Description("answer, which is going to be the email content")]
            string answer,
            ContextVariables variables)
        {
            var contract = new Email()
            {
                Address = email_addresses,
                Content = answer,
            };

            // for demo purpose only
            string emailPayload = JsonSerializer.Serialize(contract, new JsonSerializerOptions() { WriteIndented = true });
            variables["email"] = emailPayload;

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
//Executing RunExampleAsync
//Flow: FlowOrchestrator_Example_Flow
//Question: What is the tallest mountain on Earth? How tall is it divided by 2?
//Answer: The tallest mountain on Earth is Mount Everest, which is 29,031.69 feet (8,848.86 meters) above sea level. Half of its height is 14,515.845 feet (4,424.43 meters).
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
//  "Content": "The tallest mountain on Earth is Mount Everest, which is 29,031.69 feet (8,848.86 meters) above sea level. Half of its height is 14,515.845 feet (4,424.43 meters)."
//}
//Time Taken: 00:00:24.2450785
//*****************************************************

//*****************************************************
//Executing RunInteractiveAsync
//Flow: FlowOrchestrator_Example_Flow
//Please type the question you'd like to ask
//User:
//What is the length of the longest river in ireland?
//Assistant: ["Please provide a valid email address."]
//User:
//foo@bar.com
//Assistant: ["Do you want to send it to another email address?"]
//User:
//no
//Assistant: []
//        Email Address: ["foo@bar.com"]
//        Email Payload: {
//  "Address": "[\u0022foo@bar.com\u0022]",
//  "Content": "The longest river in Ireland is the River Shannon with a length of 360 km (223 miles)."
//}
//Flow completed, exiting
//Time Taken: 00:00:44.0215449
//*****************************************************
