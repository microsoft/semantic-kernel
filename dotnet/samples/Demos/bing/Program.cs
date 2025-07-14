// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Plugins.Web;
using Microsoft.SemanticKernel.Plugins.Web.QP;
using Microsoft.Extensions.Configuration;    // <-- Add this NuGet: Microsoft.Extensions.Configuration.Ini

internal sealed class Program
{
    public static async Task StartAgentModeAsync(Microsoft.SemanticKernel.Kernel kernel, string systemprompt)
    {
        var executionSettings = new OpenAIPromptExecutionSettings
        {
            Temperature = 0.7,
            TopP = 0.5,
            MaxTokens = 10000,
            FunctionChoiceBehavior = Microsoft.SemanticKernel.FunctionChoiceBehavior.Auto()
        };

        var agent = new ChatCompletionAgent()
        {
            Kernel = kernel,
            Instructions = systemprompt,
            Arguments = new KernelArguments(executionSettings)
        };

        ChatHistoryAgentThread thread = new();
        while (true)
        {
            Console.Write("You: ");
            string userInput = Console.ReadLine()?.Trim();
            if (string.Equals(userInput, "exit", StringComparison.OrdinalIgnoreCase))
            {
                break;
            }

            if (string.IsNullOrEmpty(userInput))
            {
                continue;
            }

            // ─────────────────────────────────────────────────────────────────────────
            // 5) Stream the agent's response using InvokeStreamingAsync
            //    - This overload takes: (message, thread, options, cancellationToken)
            //    - The agent's Arguments (kernel settings) are applied automatically
            // ─────────────────────────────────────────────────────────────────────────
            await foreach (var responseItem in agent.InvokeStreamingAsync(
                // Wrap the user input in a ChatMessageContent so the agent knows it's from the user
                new Microsoft.SemanticKernel.ChatMessageContent(AuthorRole.User, userInput),
                thread,
                // Use default invoke options (you can customize if needed)
                new AgentInvokeOptions(),
                // No cancellation for this example
                CancellationToken.None).ConfigureAwait(false))
            {
                // 6a) Print out the model's “thought” if present
                if (responseItem.Message.Metadata.TryGetValue("System thought", out var thought))
                {
                    Console.ForegroundColor = ConsoleColor.Yellow;
                    Console.WriteLine($"\n[MODEL THOUGHT] {thought}\n");
                    Console.ResetColor();
                }

                // 6b) Print out the next chunk of the assistant’s content
                Console.Write(responseItem.Message.Content);
            }

            Console.WriteLine("\n"); // end of turn
        }
    }

    public static async Task StartChatModeAsync(Microsoft.SemanticKernel.Kernel kernel, string systemprompt)
    {
        Console.WriteLine("Chat with the agent (type 'exit' to quit):");
        var chatCompletion = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = new ChatHistory(systemprompt);

        var executionSettings = new OpenAIPromptExecutionSettings
        {
            Temperature = 0.7,
            TopP = 0.5,
            MaxTokens = 10000,
            FunctionChoiceBehavior = Microsoft.SemanticKernel.FunctionChoiceBehavior.Auto()
        };
        while (true)
        {
            Console.Write("User: ");
            string userMessage = Console.ReadLine();
            if (string.Equals(userMessage, "exit", StringComparison.OrdinalIgnoreCase))
            {
                break;
            }
            chatHistory.AddUserMessage(userMessage);
            var answer = await chatCompletion.GetChatMessageContentAsync(chatHistory, executionSettings, kernel).ConfigureAwait(false);
            Console.WriteLine($"------------------------------------\n{answer}");
        }
    }

    public static async Task StartChatModeStreamingAsync(Microsoft.SemanticKernel.Kernel kernel, string systemprompt)
    {
        Console.WriteLine("Chat with the agent (type 'exit' to quit):");
        var chatCompletion = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = new ChatHistory(systemprompt);

        var executionSettings = new OpenAIPromptExecutionSettings
        {
            Temperature = 0.7,
            TopP = 0.5,
            MaxTokens = 10000,
            FunctionChoiceBehavior = Microsoft.SemanticKernel.FunctionChoiceBehavior.Auto()
        };

        while (true)
        {
            Console.Write("User: ");
            string userMessage = Console.ReadLine();
            if (string.Equals(userMessage, "exit", StringComparison.OrdinalIgnoreCase))
            {
                break;
            }
            chatHistory.AddUserMessage(userMessage);

            var fullMessage = new StringBuilder();
            Console.WriteLine($"\nStart Model output ------------------------------------  \n");
            await foreach (var answer in chatCompletion.GetStreamingChatMessageContentsAsync(chatHistory, executionSettings, kernel).ConfigureAwait(false))
            {
                Console.Write(answer.Content);
                fullMessage.Append(answer.Content);
            }
            // Add the full response to the chat history
            chatHistory.AddAssistantMessage(fullMessage.ToString());

            Console.WriteLine($"\nEnd Model output ------------------------------------  \n");
        }
    }
    private const string IniFileName = "systemprompt.json";

    private static async Task Main(string[] args)
    {
        var config = new ConfigurationBuilder()
            .AddJsonFile(path: IniFileName, optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .Build();

        string apiKey = config["OpenAI:apikey"];
        string endpoint = config["OpenAI:endpoint"];
        string deploymentName = config["OpenAI:deploymentname"];
        string systemprompt = config["OpenAI:systemprompt"];
        // Console.WriteLine("Please enter your Azure OpenAI endpoint:");
        //string endpoint = "https://gpt-gem-westus3.openai.azure.com/";

        // Console.WriteLine("Please enter your Azure OpenAI API key:");
        // string apiKey = "";

        // string deploymentName = "gpt-4o";


        // string bingApiKey="";

        //string deploymentName = "gpt-4o";


        var kernel = Kernel.CreateBuilder()
            .AddAzureOpenAIChatCompletion(deploymentName, endpoint, apiKey)
            .Build();

        #pragma warning disable SKEXP0050
        var bingConnector = new QPConnector("");
        kernel.ImportPluginFromObject(new WebSearchEnginePlugin(bingConnector), "WebSearch");
        #pragma warning restore SKEXP0050

        //string systemprompt = "You are a helpful assistant that reasons step-by-step.\nBefore you give your answer, list each intermediate reasoning step as:\nModel Thought: ... \nThen conclude with:\n =========\n Final Answer: <your answer>. Also you can help user find the most relevacne page using function call. Please use the search mcp tool to find 100 urls and rank them by their title and snippets. Please select final few urls out of 100 urls returned by mcp tool that you think is usefull. also try to summurize the knowledge and please add the reference.";
        int mode = 2;
        if (mode == 0)
        {
            await StartAgentModeAsync(kernel, systemprompt).ConfigureAwait(false);
        }
        else if (mode == 1)
        {
            await StartChatModeAsync(kernel, systemprompt).ConfigureAwait(false);
        }
        else if (mode == 2)
        {
            await StartChatModeStreamingAsync(kernel, systemprompt).ConfigureAwait(false);
        }
    }
}

