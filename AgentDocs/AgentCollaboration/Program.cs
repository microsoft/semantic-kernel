// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Azure.Identity;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Chat;
using Microsoft.SemanticKernel.Agents.History;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;

namespace AgentsSample;

/*****************
 * SETUP:
 * dotnet user-secrets set "OpenAISettings:ApiKey" "<api-key>"
 * dotnet user-secrets set "OpenAISettings:ChatModel" "gpt-4o"
 * dotnet user-secrets set "AzureOpenAISettings:Endpoint" "https://lightspeed-team-shared-openai-eastus.openai.azure.com/"
 * dotnet user-secrets set "AzureOpenAISettings:ChatModelDeployment" "gpt-4o"

 * INPUTS:
 * 1. 
 * 2. 
 * 3. 
 *****************/

public static class Program
{
    public static async Task Main()
    {
        // Load configuration from environment variables or user secrets.
        Settings settings = new();

        Console.WriteLine("Creating kernel...");
        IKernelBuilder builder = Kernel.CreateBuilder();

        builder.AddAzureOpenAIChatCompletion(
            settings.AzureOpenAI.ChatModelDeployment,
            settings.AzureOpenAI.Endpoint,
            new AzureCliCredential());

        Kernel kernel = builder.Build();

        OpenAIClientProvider clientProvider =
            OpenAIClientProvider.ForAzureOpenAI(new AzureCliCredential(), new Uri(settings.AzureOpenAI.Endpoint));

        Console.WriteLine("Defining agents...");

        ChatCompletionAgent agentDesigner =
            new()
            {
                Name = "Designer",
                Instructions =
                        """
                        Design a software solution and provide clear functional specification without code examples.
                        Always think about the user experience.
                        Include functional requirements and examples.
                        Where helpful, define data-flow.
                        """,
                Kernel = kernel,
                Arguments = new KernelArguments(new AzureOpenAIPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
            };

        ChatCompletionAgent agentReviewer =
            new()
            {
                Name = "Reviewer",
                Instructions =
                        """
                        Your job is to think step by step and review both design and code.
                        Only provid review feedback.

                        Do not produce functional specification.
                        Do not repeat functional specification.
                        Do not produce code or coding suggestions.
                        Do not repeat ocde.

                        Review design provide feedback for improvement.
                        Design should be clear and complete.
                        Identify any omissions or inconsistencies.
                        When the design is acceptable, say that it is acceptable.

                        Review code and provide feedback for improvement.
                        Code should meet all functional requirements from the design.
                        Code should allow for future maintenance and extension.
                        Code should always include unit-tests and a complete user experience.
                        When you don't have any more suggestions, say that it is approved.
                        If you are providing suggestions, it is explicitly not approved.
                        """,
                Kernel = kernel,
                Arguments = new KernelArguments(new AzureOpenAIPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
            };

        OpenAIAssistantAgent agentCoder =
            await OpenAIAssistantAgent.CreateAsync(
                clientProvider,
                new OpenAIAssistantDefinition(settings.AzureOpenAI.ChatModelDeployment)
                {
                    Name = "Coder",
                    Instructions =
                        """
                        Write python code based on the design input and functional requirements.
                        If the design is not clear, ask for clarification.
                        If you can improve upon the design, do so.
                        Make the code as clear and maintainable as possible.
                        Only produce code without explanation.
                        Update code based on review feedback.
                        """,
                    EnableCodeInterpreter = true
                },
                new Kernel());

        AgentGroupChat chatProvider() =>
            new(agentDesigner, agentReviewer, agentCoder)
            {
                ExecutionSettings = new AgentGroupChatSettings
                {
                    SelectionStrategy =
                        new SequentialSelectionStrategy
                        {
                            InitialAgent = agentDesigner,
                            //ChatReducer = new ChatHistorySummarizationReducer(kernel.GetRequiredService<IChatCompletionService>(), 1),
                        },
                    TerminationStrategy =
                        new RegexTerminationStrategy("(approve)")
                        {
                            Agents = [agentReviewer],
                            MaximumIterations = 12,
                        }
                }
            };
        DevelopmentTeam team = new(chatProvider);
        Kernel managerKernel = kernel.Clone();
        managerKernel.Plugins.AddFromObject(team);
        ChatCompletionAgent agentManager =
            new()
            {
                Name = "Manager",
                Instructions =
                        """
                        Collaborate with the development team of agents produce a python software solution.
                        Ask the user for critical details prior to working with the development team.
                        Save all code produced to file storage.
                        Always report fully qualified path of the any saved file.
                        When working with team to update existing code, specify the exact code you are referencing.
                        """,
                Kernel = managerKernel,
                Arguments = new KernelArguments(new AzureOpenAIPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
            };

        Console.WriteLine("Ready!");

        ChatHistory chat = [];
        try
        {
            bool isComplete = false;
            do
            {
                Console.WriteLine();
                Console.Write("> ");
                string input = Console.ReadLine();
                if (string.IsNullOrWhiteSpace(input))
                {
                    continue;
                }
                if (input.Trim().Equals("EXIT", StringComparison.OrdinalIgnoreCase))
                {
                    isComplete = true;
                    break;
                }

                chat.Add(new ChatMessageContent(AuthorRole.User, input));

                Console.WriteLine();

                await foreach (ChatMessageContent response in agentManager.InvokeAsync(chat))
                {
                    // Display response.
                    Console.Write($"{response.Content}");
                }
                Console.WriteLine();

            } while (!isComplete);
        }
        finally
        {
            Console.WriteLine();
            Console.WriteLine("Cleaning-up...");
            await Task.WhenAll(
                [
                    agentCoder.DeleteAsync(),
                ]);
        }
    }

    private sealed class DevelopmentTeam(Func<AgentGroupChat> chatProvider)
    {
        [KernelFunction]
        [Description("Save code to file storage.")]
        [return: Description("The full file path.")]
        public async Task<string> SaveCodeFileAsync(string code, string filename)
        {
            string filePath =
                Path.Combine(
                    Path.GetTempPath(),
                    Path.ChangeExtension(filename, ".py"));
            await File.WriteAllTextAsync(filePath, code);
            Process.Start(
                new ProcessStartInfo
                {
                    FileName = "cmd.exe",
                    Arguments = $"/C start {filePath}"
                });

            return filePath;
        }

        [KernelFunction]
        [Description("Collaboration with the development team to produce a software solution.")]
        public async Task<IReadOnlyCollection<ChatMessageContent>> CollaborateAsync(string input, Kernel kernel)
        {
            ConsoleColor originalColor = Console.ForegroundColor;
            AgentGroupChat chat = chatProvider();
            try
            {
                Console.ForegroundColor = ConsoleColor.Green;
                chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, input));
                Console.WriteLine(input);

                List<ChatMessageContent> responses = [];
                await foreach (ChatMessageContent response in chat.InvokeAsync())
                {
                    Console.ForegroundColor = ConsoleColor.Yellow;
                    Console.WriteLine($"{response.AuthorName}:");
                    Console.ForegroundColor = ConsoleColor.Cyan;
                    Console.WriteLine(response.Content);
                    Console.WriteLine();
                    responses.Add(response);
                }

                ChatHistorySummarizationReducer reducer =
                    new(kernel.GetRequiredService<IChatCompletionService>(), 1)
                    {
                        SummarizationInstructions =
                            """
                            Summarize the team interaction and provide an exact version of the most recent code.
                            """
                    };

                ChatMessageContent[] summary = (await reducer.ReduceAsync(responses))?.ToArray() ?? [];

                Console.ForegroundColor = ConsoleColor.Yellow;
                Console.WriteLine("Summary:");
                Console.ForegroundColor = ConsoleColor.Cyan;
                Console.WriteLine(summary[0]);

                return summary;
            }
            finally
            {
                Console.ForegroundColor = originalColor;
                await chat.ResetAsync();
            }
        }
    }
}
