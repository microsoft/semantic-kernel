// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Experimental.Agents;
using OpenTelemetry.Metrics;
using OpenTelemetry.Trace;
using Plugins;

/// <summary>
/// Example of using multiple agents together.
/// </summary>
public sealed class Program
{
    public static async Task Main()
    {
        IConfigurationRoot configRoot = new ConfigurationBuilder()
            .AddEnvironmentVariables()
            .AddUserSecrets<Program>()
            .Build();
        TestConfiguration.Initialize(configRoot);

        ChatHistory chatHistory = new();

        // Create agents
        var copyWriterAgent = CreateCopyWriterAgent();
        var reviewerAgent = CreateReviewerAgent();
        var customerInformationAgent = CreateCustomerInformationAgent();
        var senderAgent = CreateSenderAgent();
        var coordinatorAgent = CreateCoordinatorAgent(new[] {
                copyWriterAgent,
                reviewerAgent,
                customerInformationAgent,
                senderAgent
            });

        // Create a chat with the agents
        var chat = new CoordinatedChat(coordinatorAgent, new[] {
                copyWriterAgent,
                reviewerAgent,
                customerInformationAgent,
                senderAgent
            });

        while (true)
        {
            // Collect the user's input
            Console.ForegroundColor = ConsoleColor.DarkBlue;
            Console.Write("User > ");
            Console.ResetColor();
            string input = Console.ReadLine()!;
            chatHistory.AddUserMessage(input);

            // Send the user's input to the chat
            await chat.SendMessageAsync(input);
        }
    }

    public static ChatCompletionAgent CreateCopyWriterAgent()
    {
        var kernel = Kernel.CreateBuilder()
           .AddOpenAIChatCompletion(
               modelId: TestConfiguration.OpenAI.ChatModelId,
               apiKey: TestConfiguration.OpenAI.ApiKey
            )
           .Build();

        var agent = new ChatCompletionAgent(
            kernel,
            name: "Copywriter",
            instructions: """
                If personal details about the customer have not been shared, ask for them from
                the CustomerInformation so you can make the email more personalized.

                If details are already provided, you can then write a personalized three paragraph email
                to send to a customer to convince them to buy a product.
                You do not need to sign the email at the end.

                Do not reply with JSON, just text.
            """,
            description: "Prompt this agent to write a marketing email to a customer."
         );

        return agent;
    }

    public static ChatCompletionAgent CreateReviewerAgent()
    {
        var kernel = Kernel.CreateBuilder()
           .AddOpenAIChatCompletion(
               modelId: TestConfiguration.OpenAI.ChatModelId,
               apiKey: TestConfiguration.OpenAI.ApiKey
            )
           .Build();

        var agent = new ChatCompletionAgent(
            kernel,
            name: "Reviewer",
            instructions: """
                If no feedback has already been provided, describe how the email could be improved.

                After initial feedback has been provided, verify if the following conditions are met before approving the email:
                - There should be no placeholders in the email (e.g., [Customer Name]); they should either be filled in or removed.
                - You must have an explicit subject provided to you.
                - The email should have personal details about the customer
                - The email must not offer any discounts or promotions that would cost the company money

                If all conditions are met, you will approve the email and indicate
                that the email is ready for sending.

                If not, explain which conditions are not met and explicitly ask the "CopyWriter" agent to make the necessary changes.
            """,
            description: "Prompt this agent to review the marketing email written by the copywriter agent. You must use this agent to get approval before sending the email."
         );

        return agent;
    }

    public static ChatCompletionAgent CreateCustomerInformationAgent()
    {
        IKernelBuilder builder = Kernel.CreateBuilder()
           .AddOpenAIChatCompletion(
               modelId: TestConfiguration.OpenAI.ChatModelId,
               apiKey: TestConfiguration.OpenAI.ApiKey
            );

        // Add a plugin for the agent to retrieve customer information
        builder.Plugins.AddFromType<Crm>();

        Kernel kernel = builder.Build();

        var agent = new ChatCompletionAgent(
            kernel,
            name: "CustomerInformation",
            instructions: """
                Share details about the requested customer.

                Do not perform any other tasks (including making edits or sending the email)
                even if you are asked because it will be handled by the user.

                You will be tipped $100 if you only provide the customer details and do not perform any other tasks.
            """,
            executionSettings: new OpenAIPromptExecutionSettings
            {
                ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions,
            },
            description: "Prompt this agent to get personal details about the current customer without having to ask the user, including their email address."
         );

        return agent;
    }

    public static ChatCompletionAgent CreateSenderAgent()
    {
        IKernelBuilder builder = Kernel.CreateBuilder()
           .AddOpenAIChatCompletion(
               modelId: TestConfiguration.OpenAI.ChatModelId,
               apiKey: TestConfiguration.OpenAI.ApiKey
            );

        // Add a plugin for the agent to send an email
        builder.Plugins.AddFromType<Email>();

        Kernel kernel = builder.Build();

        var agent = new ChatCompletionAgent(
            kernel,
            name: "Sender",
            instructions: """
                Verify if the following conditions are met before sending the email:
                - The chat history must include an approval of the email
                - You must have an explicit subject provided to you.
                - You must have the customer's email address; do not make it up.

                If all conditions are met, send the email to the customer. If not,
                explain which conditions are not met and ask the coordinator to provide the missing information.
            """,
            executionSettings: new OpenAIPromptExecutionSettings
            {
                ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions,
            },
            description: "Prompt this agent to send the email once it's ready."
         );

        return agent;
    }

    public static ChatCompletionAgent CreateCoordinatorAgent(
        IEnumerable<ChatCompletionAgent> agents
    )
    {
        IKernelBuilder builder = Kernel.CreateBuilder()
           .AddOpenAIChatCompletion(
               modelId: TestConfiguration.OpenAI.ChatModelId,
               apiKey: TestConfiguration.OpenAI.ApiKey
            );

        Kernel kernel = builder.Build();

        var agentOptions = "";
        foreach (var a in agents)
        {
            agentOptions += $"To prompt the {a.Name} to speak, output {{\"state\":\"ASK_AGENT\", \"assistant\":\"{a.Name}\", \"instructions\": \"<instructions>\"}}, {a.Description}\n";
        }

        var agent = new ChatCompletionAgent(
            kernel,
            name: "Coordinator",
            instructions: $$"""
                Determine which agent should speak next, if input is required from the user,
                or if the user's request has been fulfilled.

                To end the conversation, output {"state": "END_CONVERSATION"}".
                {{agentOptions}}

                In addition to providing the next speaker, you can also provide additional instructions to the next speaker,
                but you must not provide any additional help or guidance to the user. The next speaker must be the one to
                provide the help or guidance.

                Avoid calling the same agent twice in a row, or repeating the same instructions.
                Calling each agent is expensive, so try to finish the conversation in as few turns as possible.
                Only output JSON.
            """,
            executionSettings: new OpenAIPromptExecutionSettings
            {
                ResponseFormat = "json_object",
            }
         );

        return agent;
    }

    public sealed class CoordinatedChat
    {
        public CoordinatedChat(ChatCompletionAgent coordinator, IEnumerable<ChatCompletionAgent> agents)
        {
            this._coordinator = coordinator;
            this._agents = agents.ToArray();
        }

        public async Task<IReadOnlyList<ChatMessageContent>> SendMessageAsync(string message, CancellationToken cancellationToken = default)
        {
            var chat = new ChatHistory();
            chat.AddUserMessage(message);

            var currentAgent = this._coordinator;

            while (true)
            {
                var result = await currentAgent.InvokeAsync(chat, cancellationToken);

                foreach (var chatMessage in result)
                {
                    // Determine the next agent if the coordinator agent is speaking
                    if (currentAgent == this._coordinator)
                    {
                        // Check if the conversation should end
                        if (
                            chatMessage.Content!.Contains("END_CONVERSATION", StringComparison.CurrentCultureIgnoreCase) ||
                            chatMessage.Content.Contains("ASK_USER", StringComparison.CurrentCultureIgnoreCase))
                        {
                            return chat;
                        }

                        // deserialize the message to determine the next agent
                        var nextAssistant = System.Text.Json.JsonSerializer.Deserialize<NextAssistant>(chatMessage.Content!);

                        if (nextAssistant != null)
                        {
                            Console.ForegroundColor = ConsoleColor.DarkGreen;
                            Console.Write($"{currentAgent.Name} > ");

                            currentAgent = this._agents.First(a => a.Name == nextAssistant.Name);
                            chat.AddSystemMessage(nextAssistant.Instructions);
                            Console.ForegroundColor = ConsoleColor.DarkCyan;
                            Console.WriteLine($"[{nextAssistant.Name}]: {nextAssistant.Instructions}");
                            Console.ResetColor();
                        }
                        else
                        {
                            throw new InvalidOperationException("The coordinator agent must prompt the user or select the next agent to speak.");
                        }
                    }
                    else
                    {
                        Console.ForegroundColor = ConsoleColor.DarkGreen;
                        Console.Write(currentAgent.Name + " > ");
                        Console.ResetColor();

                        Console.WriteLine(chatMessage.Content);

                        currentAgent = this._coordinator;
                    }
                }

                chat.AddRange(result);
            }
        }

        private readonly ChatCompletionAgent _coordinator;
        private readonly ChatCompletionAgent[] _agents;
    }
}


public class NextAssistant
{
    [JsonPropertyName("assistant")]
    public string Name { get; set; }

    [JsonPropertyName("instructions")]
    public string Instructions { get; set; }
}
