// Copyright (c) Microsoft. All rights reserved.

using Connectors.Amazon.Extensions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.TextGeneration;

// Display the available options
Console.WriteLine("Choose an option:");
Console.WriteLine("1. Chat Completion");
Console.WriteLine("2. Text Generation");
Console.WriteLine("3. Stream Chat Completion");
Console.WriteLine("4. Stream Text Generation");

Console.Write("Enter your choice (1-4): ");
int choice;
while (!int.TryParse(Console.ReadLine(), out choice) || choice < 1 || choice > 4)
{
    Console.WriteLine("Invalid input. Please enter a valid number from the list.");
    Console.Write("Enter your choice (1-4): ");
}

switch (choice)
{
    case 1:
        // ----------------------------CHAT COMPLETION----------------------------
        string userInput;
        ChatHistory chatHistory = new();

        // List of available models
        Dictionary<int, string> modelOptions = new()
        {
            { 1, "amazon.titan-text-premier-v1:0" },
            { 2, "anthropic.claude-3-sonnet-20240229-v1:0" },
            { 3, "anthropic.claude-3-haiku-20240307-v1:0" },
            { 4, "anthropic.claude-v2:1" },
            { 5, "ai21.jamba-instruct-v1:0" },
            { 6, "cohere.command-r-plus-v1:0" },
            { 7, "meta.llama3-8b-instruct-v1:0" },
            { 8, "mistral.mistral-7b-instruct-v0:2" }
        };

        // Display the model options
        Console.WriteLine("Available models:");
        foreach (var option in modelOptions)
        {
            Console.WriteLine($"{option.Key}. {option.Value}");
        }

        Console.Write("Enter the number of the model you want to use for chat completion: ");
        int chosenModel;
        while (!int.TryParse(Console.ReadLine(), out chosenModel) || !modelOptions.ContainsKey(chosenModel))
        {
            Console.WriteLine("Invalid input. Please enter a valid number from the list.");
            Console.Write("Enter the number of the model you want to use: ");
        }

        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelOptions[chosenModel]).Build();
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        do
        {
            Console.Write("Enter a prompt (or 'exit' to quit): ");
            userInput = Console.ReadLine() ?? "exit";

            if (!string.Equals(userInput, "exit", StringComparison.OrdinalIgnoreCase))
            {
                chatHistory.AddMessage(AuthorRole.User, userInput);
                var result = await chatCompletionService.GetChatMessageContentsAsync(chatHistory).ConfigureAwait(false);
                string output = "";
                foreach (var message in result)
                {
                    output += message.Content;
                    Console.WriteLine($"Chat Completion Answer: {message.Content}");
                    Console.WriteLine();
                }
                chatHistory.AddMessage(AuthorRole.Assistant, output);
            }
        } while (!string.Equals(userInput, "exit", StringComparison.OrdinalIgnoreCase));
        break;
    case 2:
        // ----------------------------TEXT GENERATION----------------------------
        // List of available text generation models
        Dictionary<int, string> textGenerationModelOptions = new()
        {
            { 1, "amazon.titan-text-premier-v1:0" },
            { 2, "mistral.mistral-7b-instruct-v0:2" },
            { 3, "ai21.jamba-instruct-v1:0" },
            { 4, "anthropic.claude-v2:1" },
            { 5, "cohere.command-text-v14" },
            { 6, "meta.llama3-8b-instruct-v1:0" },
            { 7, "cohere.command-r-plus-v1:0" },
            { 8, "ai21.j2-ultra-v1" }
        };

        // Display the text generation model options
        Console.WriteLine("Available text generation models:");
        foreach (var option in textGenerationModelOptions)
        {
            Console.WriteLine($"{option.Key}. {option.Value}");
        }

        Console.Write("Enter the number of the text generation model you want to use: ");
        int chosenTextGenerationModel;
        while (!int.TryParse(Console.ReadLine(), out chosenTextGenerationModel) || !textGenerationModelOptions.ContainsKey(chosenTextGenerationModel))
        {
            Console.WriteLine("Invalid input. Please enter a valid number from the list.");
            Console.Write("Enter the number of the text generation model you want to use: ");
        }

        Console.Write("Text Generation Prompt: ");
        string UserPrompt2 = Console.ReadLine() ?? "";

        var kernel2 = Kernel.CreateBuilder().AddBedrockTextGenerationService(textGenerationModelOptions[chosenTextGenerationModel]).Build();

        var textGenerationService = kernel2.GetRequiredService<ITextGenerationService>();
        var textGeneration = await textGenerationService.GetTextContentsAsync(UserPrompt2).ConfigureAwait(false);
        if (textGeneration.Count > 0)
        {
            var firstTextContent = textGeneration[0];
            if (firstTextContent != null)
            {
                Console.WriteLine("Text Generation Answer: " + firstTextContent.Text);
            }
            else
            {
                Console.WriteLine("Text Generation Answer: (none)");
            }
        }
        else
        {
            Console.WriteLine("Text Generation Answer: (No output text)");
        }
        break;
    case 3:
        // ----------------------------STREAM CHAT COMPLETION----------------------------
        string userInput2;
        ChatHistory chatHistory2 = new();

        // List of available stream chat completion models
        Dictionary<int, string> streamChatCompletionModelOptions = new()
        {
            { 1, "mistral.mistral-7b-instruct-v0:2" },
            { 2, "amazon.titan-text-premier-v1:0" },
            { 3, "anthropic.claude-v2" },
            { 4, "anthropic.claude-3-sonnet-20240229-v1:0" },
            { 5, "cohere.command-r-plus-v1:0" },
            { 6, "meta.llama3-8b-instruct-v1:0" }
        };

        // Display the stream chat completion model options
        Console.WriteLine("Available stream chat completion models:");
        foreach (var option in streamChatCompletionModelOptions)
        {
            Console.WriteLine($"{option.Key}. {option.Value}");
        }

        Console.Write("Enter the number of the stream chat completion model you want to use: ");
        int chosenStreamChatCompletionModel;
        while (!int.TryParse(Console.ReadLine(), out chosenStreamChatCompletionModel) || !streamChatCompletionModelOptions.ContainsKey(chosenStreamChatCompletionModel))
        {
            Console.WriteLine("Invalid input. Please enter a valid number from the list.");
            Console.Write("Enter the number of the stream chat completion model you want to use: ");
        }

        var kernel4 = Kernel.CreateBuilder().AddBedrockChatCompletionService(streamChatCompletionModelOptions[chosenStreamChatCompletionModel]).Build();
        var chatStreamCompletionService = kernel4.GetRequiredService<IChatCompletionService>();

        do
        {
            Console.Write("Enter a prompt (or 'exit' to quit): ");
            userInput2 = Console.ReadLine() ?? "exit";

            if (!string.Equals(userInput2, "exit", StringComparison.OrdinalIgnoreCase))
            {
                chatHistory2.AddMessage(AuthorRole.User, userInput2);
                var result = chatStreamCompletionService.GetStreamingChatMessageContentsAsync(chatHistory2).ConfigureAwait(false);
                string output = "";
                await foreach (var message in result)
                {
                    Console.Write($"{message.Content}");
                    Thread.Sleep(50);
                    output += message.Content;
                }
                Console.WriteLine();
                chatHistory2.AddMessage(AuthorRole.Assistant, output);
            }
        } while (!string.Equals(userInput2, "exit", StringComparison.OrdinalIgnoreCase));
        break;
    case 4:
        // ----------------------------STREAM TEXT GENERATION----------------------------
        // List of available stream text generation models
        Dictionary<int, string> streamTextGenerationModelOptions = new()
        {
            { 1, "amazon.titan-text-premier-v1:0" },
            { 2, "anthropic.claude-v2" },
            { 3, "mistral.mistral-7b-instruct-v0:2" },
            { 4, "cohere.command-text-v14" },
            { 5, "cohere.command-r-plus-v1:0" },
            { 6, "meta.llama3-8b-instruct-v1:0" }
        };

        // Display the stream text generation model options
        Console.WriteLine("Available stream text generation models:");
        foreach (var option in streamTextGenerationModelOptions)
        {
            Console.WriteLine($"{option.Key}. {option.Value}");
        }

        Console.Write("Enter the number of the stream text generation model you want to use: ");
        int chosenStreamTextGenerationModel;
        while (!int.TryParse(Console.ReadLine(), out chosenStreamTextGenerationModel) || !streamTextGenerationModelOptions.ContainsKey(chosenStreamTextGenerationModel))
        {
            Console.WriteLine("Invalid input. Please enter a valid number from the list.");
            Console.Write("Enter the number of the stream text generation model you want to use: ");
        }

        Console.Write("Stream Text Generation Prompt: ");
        string UserPrompt3 = Console.ReadLine() ?? "";

        var kernel3 = Kernel.CreateBuilder().AddBedrockTextGenerationService(streamTextGenerationModelOptions[chosenStreamTextGenerationModel]).Build();

        var streamTextGenerationService = kernel3.GetRequiredService<ITextGenerationService>();
        var streamTextGeneration = streamTextGenerationService.GetStreamingTextContentsAsync(UserPrompt3).ConfigureAwait(true);
        await foreach (var textContent in streamTextGeneration)
        {
            Console.Write(textContent.Text);
            Thread.Sleep(50);
        }

        Console.WriteLine();
        break;
}
