// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Linq;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Experimental.Orchestration;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Plugins.Core;
using Microsoft.SemanticKernel.Plugins.Web;
using Microsoft.SemanticKernel.Plugins.Web.Bing;

/**
 * This example shows how to use FlowOrchestrator to execute a given flow with interaction with client.
 */

// ReSharper disable once InconsistentNaming
public static class Example57_FlowOrchestrator
{
    private static readonly Flow s_flow = FlowSerializer.DeserializeFromYaml(@"
name: FlowOrchestrator_Example_Flow
goal: answer question and send email
steps:
  - goal: Who is the current president of the United States? What is his current age divided by 2
    skills:
      - WebSearchEnginePlugin
      - TimePlugin
    provides:
      - answer
  - goal: Collect email address
    skills:
      - CollectEmailPlugin
    completionType: AtLeastOnce
    transitionMessage: do you want to send it to another email address?
    provides:
      - email_address

  - goal: Send email
    skills:
      - SendEmail
    requires:
      - email_address
      - answer
    provides:
      - email
");

    public static Task RunAsync()
    {
        return RunExampleAsync();
        // return RunInteractiveAsync();
    }

    public static async Task RunInteractiveAsync()
    {
        var bingConnector = new BingConnector(TestConfiguration.Bing.ApiKey);
        var webSearchEnginePlugin = new WebSearchEnginePlugin(bingConnector);
        Dictionary<object, string?> skills = new()
        {
            { webSearchEnginePlugin, "WebSearch" },
            { new TimePlugin(), "time" }
        };

        FlowOrchestrator orchestrator = new(GetKernelBuilder(), await FlowStatusProvider.ConnectAsync(new VolatileMemoryStore()).ConfigureAwait(false), skills);
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

            if (input is null)
            {
                input = string.Empty;
            }
            else if (string.IsNullOrEmpty(input))
            {
                Console.WriteLine("User: ");
                input = Console.ReadLine() ?? string.Empty;
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
        var webSearchEngineSkill = new WebSearchEnginePlugin(bingConnector);
        Dictionary<object, string?> skills = new()
        {
            { webSearchEngineSkill, "WebSearch" },
            { new TimePlugin(), "time" }
        };

        FlowOrchestrator orchestrator = new(GetKernelBuilder(), await FlowStatusProvider.ConnectAsync(new VolatileMemoryStore()).ConfigureAwait(false), skills);
        var sessionId = Guid.NewGuid().ToString();

        Console.WriteLine("*****************************************************");
        Stopwatch sw = new();
        sw.Start();
        Console.WriteLine("Flow: " + s_flow.Name);
        var result = await orchestrator.ExecuteFlowAsync(s_flow, sessionId, "Execute the flow").ConfigureAwait(false);
        Console.WriteLine("Assistant: " + result.ToString());
        Console.WriteLine("\tAnswer: " + result["answer"]);

        string[] userInputs = new[]
        {
            "my email is bad*email&address",
            "my email is sample@xyz.com",
            "yes", // confirm to add another email address
            "I also want to notify foo@bar.com",
            "no", // end of collect emails
        };

        foreach (var t in userInputs)
        {
            Console.WriteLine($"User: {t}");
            result = await orchestrator.ExecuteFlowAsync(s_flow, sessionId, t).ConfigureAwait(false);
            Console.WriteLine("Assistant: " + result.ToString());
        }

        Console.WriteLine("\tEmail Address: " + result["email_address"]);
        Console.WriteLine("\tEmail Payload: " + result["email"]);

        Console.WriteLine("Time Taken: " + sw.Elapsed);
        Console.WriteLine("*****************************************************");
    }

    private static KernelBuilder GetKernelBuilder()
    {
        var builder = new KernelBuilder();

        return builder.WithAzureChatCompletionService(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey,
                alsoAsTextCompletion: true,
                setAsDefault: true)
            .WithRetryBasic(new()
            {
                MaxRetryCount = 3,
                UseExponentialBackoff = true,
                MinRetryDelay = TimeSpan.FromSeconds(3),
            });
    }

    public sealed class CollectEmailPlugin
    {
        private const string Goal = "Prompt user to provide a valid email address";

        private const string EmailRegex = @"^([\w\.\-]+)@([\w\-]+)((\.(\w){2,3})+)$";

        private const string SystemPrompt =
            $@"I am AI assistant and will only answer questions related to collect email.
The email should conform the regex: {EmailRegex}

If I cannot answer, say that I don't know.
";

        private readonly IChatCompletion _chat;

        private int MaxTokens { get; set; } = 256;

        private readonly AIRequestSettings _chatRequestSettings;

        public CollectEmailPlugin(IKernel kernel)
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
        [Description("This function is used to prompt user to provide a valid email address.")]
        [SKName("CollectEmailAddress")]
        public async Task<string> CollectEmailAsync(
            [SKName("email")] [Description("The email address provided by the user")]
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
                context.Variables["email_address"] = email;

                return "Thanks for providing the info, the following email would be used in subsequent steps: " + email;
            }

            context.Variables["email_address"] = string.Empty;
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

    public sealed class SendEmailSkill
    {
        [SKFunction]
        [Description("Send email")]
        [SKName("SendEmail")]
        public string SendEmail(
            [SKName("email_address")] string emailAddress,
            [SKName("answer")] string answer,
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
//Assistant: ["Please provide a valid email address in the following format: example@example.com"]
//        Answer: Joe Biden is the current president of the United States. His age is (2023 - 1942) = 81 years old. When divided by 2, his age is 40.5 years.
//User: my email is bad*email&address
//Assistant: ["The email address you provided is not valid. Please provide a valid email address in the following format: example@example.com"]
//User: my email is sample@xyz.com
//Assistant: ["Do you want to send it to another email address?"]
//User: yes
//Assistant: ["Please provide a valid email address in the following format: example@example.com"]
//User: I also want to notify foo@bar.com
//Assistant: ["Do you want to send it to another email address?"]
//User: no
//Assistant: []
//        Email Address: ["The collected email address is sample@xyz.com.","foo@bar.com"]
//        Email Payload: {
//  "Address": "[\u0022sample@xyz.com\u0022,\u0022foo@bar.com\u0022]",
//  "Content": "Joe Biden is the current president of the United States. His age is (2023 - 1942) = 81 years old. When divided by 2, his age is 40.5 years."
//}
//Time Taken: 00:01:15.1529717
//*****************************************************
