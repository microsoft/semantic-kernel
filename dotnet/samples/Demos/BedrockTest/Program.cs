// Copyright (c) Microsoft. All rights reserved.

using Connectors.Amazon.Extensions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.TextGeneration;

// List of available models
Dictionary<int, string> bedrockModels = new()
{
    { 1, "anthropic.claude-v2" },
    { 2, "anthropic.claude-v2:1" },
    { 3, "anthropic.claude-instant-v1" },
    { 4, "anthropic.claude-3-sonnet-20240229-v1:0" },
    { 5, "anthropic.claude-3-haiku-20240307-v1:0" },
    { 6, "cohere.command-light-text-v14" },
    { 7, "cohere.command-text-v14" },
    { 8, "cohere.command-r-v1:0" },
    { 9, "cohere.command-r-plus-v1:0" },
    { 10, "ai21.jamba-instruct-v1:0" },
    { 11, "ai21.j2-mid-v1" },
    { 12, "ai21.j2-ultra-v1" },
    { 13, "meta.llama3-8b-instruct-v1:0" },
    { 14, "meta.llama3-70b-instruct-v1:0" },
    { 15, "mistral.mistral-7b-instruct-v0:2" },
    { 16, "mistral.mixtral-8x7b-instruct-v0:1" },
    { 17, "mistral.mistral-large-2402-v1:0" },
    { 18, "mistral.mistral-small-2402-v1:0" },
    { 19, "amazon.titan-text-lite-v1" },
    { 20, "amazon.titan-text-express-v1" },
    { 21, "amazon.titan-text-premier-v1:0" }
};

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
        await PerformChatCompletion().ConfigureAwait(false);
        break;
    case 2:
        await PerformTextGeneration().ConfigureAwait(false);
        break;
    case 3:
        await PerformStreamChatCompletion().ConfigureAwait(false);
        break;
    case 4:
        await PerformStreamTextGeneration().ConfigureAwait(false);
        break;
}

async Task PerformChatCompletion()
{
    string userInput;
    ChatHistory chatHistory = new();

    // List of models to skip (does not support chat completion)
    List<int> modelsToSkip = new() { 6, 7, 11, 12 };

    // Display the model options
    Console.WriteLine("Available models:");
    foreach (var option in bedrockModels)
    {
        Console.WriteLine($"{option.Key}. {option.Value}");
    }

    Console.Write("Enter the number of the model you want to use for chat completion: ");
    int chosenModel;
    while (!int.TryParse(Console.ReadLine(), out chosenModel) || !bedrockModels.ContainsKey(chosenModel) || modelsToSkip.Contains(chosenModel))
    {
        Console.WriteLine("Invalid input. Please enter a valid number from the list (6, 7, 11, and 12 are not supported).");
        Console.Write("Enter the number of the model you want to use: ");
    }

    var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(bedrockModels[chosenModel]).Build();
    var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

    do
    {
        Console.Write("Enter a prompt (or leave empty to quit): ");
        userInput = Console.ReadLine() ?? string.Empty;

        if (!string.IsNullOrEmpty(userInput))
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
    } while (!string.IsNullOrEmpty(userInput));
}

async Task PerformTextGeneration()
{
        // Display the text generation model options
        Console.WriteLine("Available text generation models:");
        foreach (var option in bedrockModels)
        {
            Console.WriteLine($"{option.Key}. {option.Value}");
        }

        Console.Write("Enter the number of the text generation model you want to use: ");
        int chosenTextGenerationModel;
        while (!int.TryParse(Console.ReadLine(), out chosenTextGenerationModel) || !bedrockModels.ContainsKey(chosenTextGenerationModel))
        {
            Console.WriteLine("Invalid input. Please enter a valid number from the list.");
            Console.Write("Enter the number of the text generation model you want to use: ");
        }

        Console.Write("Text Generation Prompt: ");
        string userTextPrompt = Console.ReadLine() ?? "";

        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(bedrockModels[chosenTextGenerationModel]).Build();

        var textGenerationService = kernel.GetRequiredService<ITextGenerationService>();
        var textGeneration = await textGenerationService.GetTextContentsAsync(userTextPrompt).ConfigureAwait(false);
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
}

async Task PerformStreamChatCompletion()
{
    string userInput2;
        ChatHistory streamChatHistory = new();

        // List of models to skip (does not support stream chat completion)
        List<int> modelsToSkip = new() { 6, 7, 10, 11, 12 };

        // Display the stream chat completion model options
        Console.WriteLine("Available stream chat completion models:");
        foreach (var option in bedrockModels)
        {
            Console.WriteLine($"{option.Key}. {option.Value}");
        }

        Console.Write("Enter the number of the stream chat completion model you want to use: ");
        int chosenStreamChatCompletionModel;
        while (!int.TryParse(Console.ReadLine(), out chosenStreamChatCompletionModel) || !bedrockModels.ContainsKey(chosenStreamChatCompletionModel) || modelsToSkip.Contains(chosenStreamChatCompletionModel))
        {
            Console.WriteLine("Invalid input. Please enter a valid number from the list. Models 6, 7, 10, 11, and 12 are not supported.");
            Console.Write("Enter the number of the stream chat completion model you want to use: ");
        }

        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(bedrockModels[chosenStreamChatCompletionModel]).Build();
        var chatStreamCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        do
        {
            Console.Write("Enter a prompt (or leave empty to quit): ");
            userInput2 = Console.ReadLine() ?? string.Empty;

            if (!string.IsNullOrEmpty(userInput2))
            {
                streamChatHistory.AddMessage(AuthorRole.User, userInput2);
                var result = chatStreamCompletionService.GetStreamingChatMessageContentsAsync(streamChatHistory).ConfigureAwait(false);
                string output = "";
                await foreach (var message in result)
                {
                    Console.Write($"{message.Content}");
                    output += message.Content;
                }

                Console.WriteLine();
                streamChatHistory.AddMessage(AuthorRole.Assistant, output);
            }
        } while (!string.IsNullOrEmpty(userInput2));
}

async Task PerformStreamTextGeneration()
{
    // List of models to skip (does not support streaming)
    List<int> modelsToSkip = new() { 11, 12 };

    // Display the stream text generation model options
    Console.WriteLine("Available stream text generation models:");
    foreach (var option in bedrockModels)
    {
        Console.WriteLine($"{option.Key}. {option.Value}");
    }

    Console.Write("Enter the number of the stream text generation model you want to use: ");
    int chosenStreamTextGenerationModel;
    while (!int.TryParse(Console.ReadLine(), out chosenStreamTextGenerationModel) || !bedrockModels.ContainsKey(chosenStreamTextGenerationModel) || modelsToSkip.Contains(chosenStreamTextGenerationModel))
    {
        Console.WriteLine("Invalid input. Please enter a valid number from the list. Models 11 and 12 not supported for this service.");
        Console.Write("Enter the number of the stream text generation model you want to use: ");
    }

    Console.Write("Stream Text Generation Prompt: ");
    string userStreamTextPrompt = Console.ReadLine() ?? "";

    var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(bedrockModels[chosenStreamTextGenerationModel]).Build();

    var streamTextGenerationService = kernel.GetRequiredService<ITextGenerationService>();
    var streamTextGeneration = streamTextGenerationService.GetStreamingTextContentsAsync(userStreamTextPrompt).ConfigureAwait(true);
    await foreach (var textContent in streamTextGeneration)
    {
        Console.Write(textContent.Text);
    }

    Console.WriteLine();
}
