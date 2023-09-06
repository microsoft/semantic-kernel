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
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Planning.Flow;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Skills.Core;
using Microsoft.SemanticKernel.Skills.Web;
using Microsoft.SemanticKernel.Skills.Web.Bing;

/**
 * This example shows how to use FlowPlanner to execute a given flow with interaction with client.
 */

// ReSharper disable once InconsistentNaming
public static class Example55_FlowPlanner
{
    private static readonly Flow s_flow = FlowSerializer.DeserializeFromYaml(@"
name: FlowPlanner_Example_Flow
goal: answer question and send email
steps:
  - goal: Who is the current president of the United States? What is his current age divided by 2
    skills:
      - WebSearchEngineSkill
      - TimeSkill
    provides:
      - answer
  - goal: Collect email address
    skills:
      - CollectEmailSkill
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
        var webSearchEngineSkill = new WebSearchEngineSkill(bingConnector);
        Dictionary<object, string?> skills = new()
        {
            { webSearchEngineSkill, "WebSearch" },
            { new TimeSkill(), "time" }
        };

        FlowPlanner planner = new(GetKernelBuilder(), new FlowStatusProvider(new VolatileMemoryStore()), skills);
        var sessionId = Guid.NewGuid().ToString();

        Console.WriteLine("*****************************************************");
        Stopwatch sw = new();
        sw.Start();
        Console.WriteLine("Flow: " + s_flow.Name);
        SKContext? result = null;
        string? input = null;// "Execute the flow";// can this be empty?
        do
        {
            if (result is not null)
            {
                Console.WriteLine("Assistant: " + result.Result);
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

            result = await planner.ExecuteFlowAsync(s_flow, sessionId, input);
        } while (!string.IsNullOrEmpty(result.Result) && result.Result != "[]");

        Console.WriteLine("Assistant: " + result.Variables["answer"]);

        Console.WriteLine("Time Taken: " + sw.Elapsed);
        Console.WriteLine("*****************************************************");
    }

    public static async Task RunExampleAsync()
    {
        var bingConnector = new BingConnector(TestConfiguration.Bing.ApiKey);
        var webSearchEngineSkill = new WebSearchEngineSkill(bingConnector);
        Dictionary<object, string?> skills = new()
        {
            { webSearchEngineSkill, "WebSearch" },
            { new TimeSkill(), "time" }
        };

        FlowPlanner planner = new(GetKernelBuilder(), new FlowStatusProvider(new VolatileMemoryStore()), skills);
        var sessionId = Guid.NewGuid().ToString();

        Console.WriteLine("*****************************************************");
        Stopwatch sw = new();
        sw.Start();
        Console.WriteLine("Flow: " + s_flow.Name);
        var result = await planner.ExecuteFlowAsync(s_flow, sessionId, "Execute the flow");
        Console.WriteLine("Assistant: " + result.Result);
        Console.WriteLine("\tAnswer: " + result.Variables["answer"]);

        string input = "my email is bad*email&address";
        Console.WriteLine($"User: {input}");
        result = await planner.ExecuteFlowAsync(s_flow, sessionId, input);
        Console.WriteLine("Assistant: " + result.Result);

        input = "my email is sample@xyz.com";
        Console.WriteLine($"User: {input}");
        result = await planner.ExecuteFlowAsync(s_flow, sessionId, input);
        Console.WriteLine("\tEmail Address: " + result.Variables["email_address"]);
        Console.WriteLine("\tEmail Payload: " + result.Variables["email"]);

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

    public sealed class CollectEmailSkill : ChatSkill
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

        private readonly ChatRequestSettings _chatRequestSettings;

        public CollectEmailSkill(IKernel kernel)
        {
            this._chat = kernel.GetService<IChatCompletion>();
            this._chatRequestSettings = new ChatRequestSettings
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
            [SKName("email")] string email,
            SKContext context)
        {
            var chat = this._chat.CreateNewChat(SystemPrompt);
            chat.AddUserMessage(Goal);

            ChatHistory? chatHistory = this.GetChatHistory(context);
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
            this.PromptInput(context);

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
//Flow: FlowPlanner_Example_Flow
//Assistant: ["Please provide a valid email address in the following format: example@example.com"]
//        Answer: The current president of the United States is Joe Biden. His current age divided by 2 is 39.
//User: my email is bad*email&address
//Assistant: ["The email address you provided is not valid. Please provide a valid email address in the following format: example@example.com"]
//User: my email is sample@xyz.com
//        Email Address: The collected email address is sample@xyz.com.
//        Email Payload: {
//  "Address": "sample@xyz.com",
//  "Content": "The current president of the United States is Joe Biden. His current age divided by 2 is 39."
//}
//Time Taken: 00:01:05.3375146
//*****************************************************
