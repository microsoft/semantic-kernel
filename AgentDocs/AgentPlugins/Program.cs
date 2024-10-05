// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Azure.Identity;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Plugins;

namespace AgentsSample;

/*****************
 * SETUP:
 * dotnet user-secrets set "OpenAISettings:ApiKey" "<api-key>"
 * dotnet user-secrets set "OpenAISettings:ChatModel" "gpt-4o"
 * dotnet user-secrets set "AzureOpenAISettings:Endpoint" "https://lightspeed-team-shared-openai-eastus.openai.azure.com/"
 * dotnet user-secrets set "AzureOpenAISettings:ChatModelDeployment" "gpt-4o"
 * dotnet user-secrets set "GitHubSettings:BaseUrl" "https://api.github.com"
 * dotnet user-secrets set "GitHubSettings:Token" "<personal access token>"
 * 
 * INPUTS:
 * 1. What is my username?
 * 2. Describe the repo.
 * 3. Describe the newest issue created in the repo.
 * 4. List the top 10 issues closed within the last week.
 * 5. How were these issues labeled?
 * 6. List the 5 most recently opened issues with the "Agents" label
 ******************/

public static class Program
{
    public static async Task Main()
    {
        // Load configuration from environment variables or user secrets.
        Settings settings = new();

        Console.WriteLine("Initialize plugins...");
        GitHubSettings githubSettings = settings.GetSettings<GitHubSettings>();
        GitHubPlugin githubPlugin = new(githubSettings);

        Console.WriteLine("Creating kernel...");
        IKernelBuilder builder = Kernel.CreateBuilder();

        builder.AddAzureOpenAIChatCompletion(
            settings.AzureOpenAI.ChatModelDeployment,
            settings.AzureOpenAI.Endpoint,
            new AzureCliCredential());

        builder.Plugins.AddFromObject(githubPlugin);

        Kernel kernel = builder.Build();

        Console.WriteLine("Defining agent...");
        ChatCompletionAgent agent =
            new()
            {
                Name = "SampleAssistantAgent",
                Instructions =
                        """
                            You are an agent designed to query and retrieve information from a single GitHub repository in a read-only manner.
                            You are also able to access the profile of the active user.

                            Use the current date and time to provide up-to-date details or time-sensitive responses.
                        
                            The repository you are querying is a public repository with the following name: {{$repository}}

                            The current date and time is: {{$now}}. 
                            """,
                Kernel = kernel,
                Arguments =
                    new KernelArguments(new AzureOpenAIPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() })
                    {
                            { "repository", "microsoft/semantic-kernel" }
                    }
            };

        Console.WriteLine("Ready!");

        ChatHistory history = [];
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

            history.Add(new ChatMessageContent(AuthorRole.User, input));

            Console.WriteLine();

            DateTime now = DateTime.Now;
            KernelArguments arguments =
                new(new AzureOpenAIPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }) // NOTE: Update after bug fix available
                {
                    { "repository", "microsoft/semantic-kernel" }, // NOTE: Remove after bug fix available
                    { "now", $"{now.ToShortDateString()} {now.ToShortTimeString()}" }
                };
            await foreach (ChatMessageContent response in agent.InvokeAsync(history, arguments))
            {
                // Display response.
                Console.WriteLine($"{response.Content}");
            }

        } while (!isComplete);
    }
}
