// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Amazon.BedrockRuntime.Model;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.TextGeneration;

// List of available models
Dictionary<int, ModelDefinition> bedrockModels = GetBedrockModels();

// Get user choice
int choice = GetUserChoice();

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
    default:
        throw new InvalidOperationException("Invalid choice");
}

async Task PerformChatCompletion()
{
    string userInput;
    ChatHistory chatHistory = [];

    // Get available chat completion models
    var availableChatModels = bedrockModels.Values
        .Where(m => m.Modalities.Contains(ModelDefinition.SupportedModality.ChatCompletion))
        .ToDictionary(m => bedrockModels.Single(kvp => kvp.Value.Name == m.Name).Key, m => m.Name);

    // Show user what models are available and let them choose
    int chosenModel = GetModelNumber(availableChatModels, "chat completion");

    var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(availableChatModels[chosenModel]).Build();
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
                var innerContent = message.InnerContent as ConverseResponse;
                Console.WriteLine($"Usage Metadata: {JsonSerializer.Serialize(innerContent?.Usage)}");
                Console.WriteLine();
            }

            chatHistory.AddMessage(AuthorRole.Assistant, output);
        }
    } while (!string.IsNullOrEmpty(userInput));
}

async Task PerformTextGeneration()
{
    // Get available text generation models
    var availableTextGenerationModels = bedrockModels.Values
        .Where(m => m.Modalities.Contains(ModelDefinition.SupportedModality.TextCompletion))
        .ToDictionary(m => bedrockModels.Single(kvp => kvp.Value.Name == m.Name).Key, m => m.Name);

    // Show user what models are available and let them choose
    int chosenTextGenerationModel = GetModelNumber(availableTextGenerationModels, "text generation");

    Console.Write("Text Generation Prompt: ");
    string userTextPrompt = Console.ReadLine() ?? "";

    var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(availableTextGenerationModels[chosenTextGenerationModel]).Build();

    var textGenerationService = kernel.GetRequiredService<ITextGenerationService>();
    var textGeneration = await textGenerationService.GetTextContentsAsync(userTextPrompt).ConfigureAwait(false);
    if (textGeneration.Count > 0)
    {
        var firstTextContent = textGeneration[0];
        if (firstTextContent != null)
        {
            Console.WriteLine("Text Generation Answer: " + firstTextContent.Text);
            Console.WriteLine($"Metadata: {JsonSerializer.Serialize(firstTextContent.InnerContent)}");
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
    string userInput;
    ChatHistory streamChatHistory = [];

    // Get available streaming chat completion models
    var availableStreamingChatModels = bedrockModels.Values
        .Where(m => m.Modalities.Contains(ModelDefinition.SupportedModality.ChatCompletion) && m.CanStream)
        .ToDictionary(m => bedrockModels.Single(kvp => kvp.Value.Name == m.Name).Key, m => m.Name);

    // Show user what models are available and let them choose
    int chosenStreamChatCompletionModel = GetModelNumber(availableStreamingChatModels, "stream chat completion");

    var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(availableStreamingChatModels[chosenStreamChatCompletionModel]).Build();
    var chatStreamCompletionService = kernel.GetRequiredService<IChatCompletionService>();

    do
    {
        Console.Write("Enter a prompt (or leave empty to quit): ");
        userInput = Console.ReadLine() ?? string.Empty;

        if (!string.IsNullOrEmpty(userInput))
        {
            streamChatHistory.AddMessage(AuthorRole.User, userInput);
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
    } while (!string.IsNullOrEmpty(userInput));
}

async Task PerformStreamTextGeneration()
{
    // Get available streaming text generation models
    var availableStreamingTextGenerationModels = bedrockModels.Values
        .Where(m => m.Modalities.Contains(ModelDefinition.SupportedModality.TextCompletion) && m.CanStream)
        .ToDictionary(m => bedrockModels.Single(kvp => kvp.Value.Name == m.Name).Key, m => m.Name);

    // Show user what models are available and let them choose
    int chosenStreamTextGenerationModel = GetModelNumber(availableStreamingTextGenerationModels, "stream text generation");

    Console.Write("Stream Text Generation Prompt: ");
    string userStreamTextPrompt = Console.ReadLine() ?? "";

    var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(availableStreamingTextGenerationModels[chosenStreamTextGenerationModel]).Build();

    var streamTextGenerationService = kernel.GetRequiredService<ITextGenerationService>();
    var streamTextGeneration = streamTextGenerationService.GetStreamingTextContentsAsync(userStreamTextPrompt).ConfigureAwait(true);
    await foreach (var textContent in streamTextGeneration)
    {
        Console.Write(textContent.Text);
    }

    Console.WriteLine();
}

// Get the user's model choice
int GetUserChoice()
{
    int pick;

    // Display the available options
    Console.WriteLine("Choose an option:");
    Console.WriteLine("1. Chat Completion");
    Console.WriteLine("2. Text Generation");
    Console.WriteLine("3. Stream Chat Completion");
    Console.WriteLine("4. Stream Text Generation");

    Console.Write("Enter your choice (1-4): ");
    while (!int.TryParse(Console.ReadLine(), out pick) || pick < 1 || pick > 4)
    {
        Console.WriteLine("Invalid input. Please enter a valid number from the list.");
        Console.Write("Enter your choice (1-4): ");
    }

    return pick;
}

int GetModelNumber(Dictionary<int, string> availableModels, string serviceType)
{
    int chosenModel;

    // Display the model options
    Console.WriteLine($"Available {serviceType} models:");
    foreach (var option in availableModels)
    {
        Console.WriteLine($"{option.Key}. {option.Value}");
    }

    Console.Write($"Enter the number of the model you want to use for {serviceType}: ");
    while (!int.TryParse(Console.ReadLine(), out chosenModel) || !availableModels.ContainsKey(chosenModel))
    {
        Console.WriteLine("Invalid input. Please enter a valid number from the list.");
        Console.Write($"Enter the number of the model you want to use for {serviceType}: ");
    }

    return chosenModel;
}

Dictionary<int, ModelDefinition> GetBedrockModels()
{
    return new Dictionary<int, ModelDefinition>
    {
        { 1, new ModelDefinition { Modalities = [ModelDefinition.SupportedModality.ChatCompletion, ModelDefinition.SupportedModality.TextCompletion], Name = "anthropic.claude-v2", CanStream = true } },
        { 2, new ModelDefinition { Modalities = [ModelDefinition.SupportedModality.ChatCompletion, ModelDefinition.SupportedModality.TextCompletion], Name = "anthropic.claude-v2:1", CanStream = true } },
        { 3, new ModelDefinition { Modalities = [ModelDefinition.SupportedModality.ChatCompletion, ModelDefinition.SupportedModality.TextCompletion], Name = "anthropic.claude-instant-v1", CanStream = false } },
        { 4, new ModelDefinition { Modalities = [ModelDefinition.SupportedModality.ChatCompletion, ModelDefinition.SupportedModality.TextCompletion], Name = "anthropic.claude-3-sonnet-20240229-v1:0", CanStream = false } },
        { 5, new ModelDefinition { Modalities = [ModelDefinition.SupportedModality.ChatCompletion, ModelDefinition.SupportedModality.TextCompletion], Name = "anthropic.claude-3-haiku-20240307-v1:0", CanStream = false } },
        { 6, new ModelDefinition { Modalities = [ModelDefinition.SupportedModality.TextCompletion], Name = "cohere.command-light-text-v14", CanStream = false } },
        { 7, new ModelDefinition { Modalities = [ModelDefinition.SupportedModality.TextCompletion], Name = "cohere.command-text-v14", CanStream = false } },
        { 8, new ModelDefinition { Modalities = [ModelDefinition.SupportedModality.ChatCompletion, ModelDefinition.SupportedModality.TextCompletion], Name = "cohere.command-r-v1:0", CanStream = true } },
        { 9, new ModelDefinition { Modalities = [ModelDefinition.SupportedModality.ChatCompletion, ModelDefinition.SupportedModality.TextCompletion], Name = "cohere.command-r-plus-v1:0", CanStream = true } },
        { 10, new ModelDefinition { Modalities = [ModelDefinition.SupportedModality.ChatCompletion, ModelDefinition.SupportedModality.TextCompletion], Name = "ai21.jamba-instruct-v1:0", CanStream = true } },
        { 11, new ModelDefinition { Modalities = [ModelDefinition.SupportedModality.TextCompletion], Name = "ai21.j2-mid-v1", CanStream = false } },
        { 12, new ModelDefinition { Modalities = [ModelDefinition.SupportedModality.TextCompletion], Name = "ai21.j2-ultra-v1", CanStream = false } },
        { 13, new ModelDefinition { Modalities = [ModelDefinition.SupportedModality.ChatCompletion, ModelDefinition.SupportedModality.TextCompletion], Name = "meta.llama3-8b-instruct-v1:0", CanStream = true } },
        { 14, new ModelDefinition { Modalities = [ModelDefinition.SupportedModality.ChatCompletion, ModelDefinition.SupportedModality.TextCompletion], Name = "meta.llama3-70b-instruct-v1:0", CanStream = true } },
        { 15, new ModelDefinition { Modalities = [ModelDefinition.SupportedModality.ChatCompletion, ModelDefinition.SupportedModality.TextCompletion], Name = "mistral.mistral-7b-instruct-v0:2", CanStream = true } },
        { 16, new ModelDefinition { Modalities = [ModelDefinition.SupportedModality.ChatCompletion, ModelDefinition.SupportedModality.TextCompletion], Name = "mistral.mixtral-8x7b-instruct-v0:1", CanStream = true } },
        { 17, new ModelDefinition { Modalities = [ModelDefinition.SupportedModality.ChatCompletion, ModelDefinition.SupportedModality.TextCompletion], Name = "mistral.mistral-large-2402-v1:0", CanStream = true } },
        { 18, new ModelDefinition { Modalities = [ModelDefinition.SupportedModality.ChatCompletion, ModelDefinition.SupportedModality.TextCompletion], Name = "mistral.mistral-small-2402-v1:0", CanStream = true } },
        { 19, new ModelDefinition { Modalities = [ModelDefinition.SupportedModality.ChatCompletion, ModelDefinition.SupportedModality.TextCompletion], Name = "amazon.titan-text-lite-v1", CanStream = true } },
        { 20, new ModelDefinition { Modalities = [ModelDefinition.SupportedModality.ChatCompletion, ModelDefinition.SupportedModality.TextCompletion], Name = "amazon.titan-text-express-v1", CanStream = true } },
        { 21, new ModelDefinition { Modalities = [ModelDefinition.SupportedModality.ChatCompletion, ModelDefinition.SupportedModality.TextCompletion], Name = "amazon.titan-text-premier-v1:0", CanStream = true } }
    };
}

/// <summary>
/// ModelDefinition.
/// </summary>
internal struct ModelDefinition
{
    /// <summary>
    /// List of services that the model supports.
    /// </summary>
    internal List<SupportedModality> Modalities { get; set; }
    /// <summary>
    /// Model ID.
    /// </summary>
    internal string Name { get; set; }
    /// <summary>
    /// If the model supports streaming.
    /// </summary>
    internal bool CanStream { get; set; }

    /// <summary>
    /// The services the model supports.
    /// </summary>
    internal enum SupportedModality
    {
        /// <summary>
        /// Text completion service.
        /// </summary>
        TextCompletion,
        /// <summary>
        /// Chat completion service.
        /// </summary>
        ChatCompletion
    }
}
