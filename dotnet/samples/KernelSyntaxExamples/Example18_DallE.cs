// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.ImageGeneration;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using RepoUtils;

/**
 * The following example shows how to use Semantic Kernel with OpenAI Dall-E 2 to create images
 */

// ReSharper disable once InconsistentNaming
public static class Example18_DallE
{
    public static async Task RunAsync()
    {
        await OpenAIDallEAsync();
        await AzureOpenAIDallEAsync();
    }

    private static async Task OpenAIDallEAsync()
    {
        Console.WriteLine("======== OpenAI Dall-E 2 Image Generation ========");

        IKernel kernel = new KernelBuilder()
            .WithLogger(ConsoleLogger.Log)
            // Add your image generation service
            .WithOpenAIImageGenerationService(Env.Var("OPENAI_API_KEY"))
            // Add your chat completion service 
            .WithOpenAIChatCompletionService("gpt-3.5-turbo", Env.Var("OPENAI_API_KEY"))
            .Build();

        IImageGeneration dallE = kernel.GetService<IImageGeneration>();

        var imageDescription = "A cute baby sea otter";
        var image = await dallE.GenerateImageAsync(imageDescription, 256, 256);

        Console.WriteLine(imageDescription);
        Console.WriteLine("Image URL: " + image);

        /* Output:

        A cute baby sea otter
        Image URL: https://oaidalleapiprodscus.blob.core.windows.net/private/....

        */

        Console.WriteLine("======== Chat with images ========");

        IChatCompletion chatGPT = kernel.GetService<IChatCompletion>();
        var chatHistory = chatGPT.CreateNewChat(
            "You're chatting with a user. Instead of replying directly to the user" +
            " provide the description of an image that expresses what you want to say." +
            " The user won't see your message, they will see only the image. The system " +
            " generates an image using your description, so it's important you describe the image with details.");

        var msg = "Hi, I'm from Tokyo, where are you from?";
        chatHistory.AddUserMessage(msg);
        Console.WriteLine("User: " + msg);

        string reply = await chatGPT.GenerateMessageAsync(chatHistory);
        chatHistory.AddAssistantMessage(reply);
        image = await dallE.GenerateImageAsync(reply, 256, 256);
        Console.WriteLine("Bot: " + image);
        Console.WriteLine("Img description: " + reply);

        msg = "Oh, wow. Not sure where that is, could you provide more details?";
        chatHistory.AddUserMessage(msg);
        Console.WriteLine("User: " + msg);

        reply = await chatGPT.GenerateMessageAsync(chatHistory);
        chatHistory.AddAssistantMessage(reply);
        image = await dallE.GenerateImageAsync(reply, 256, 256);
        Console.WriteLine("Bot: " + image);
        Console.WriteLine("Img description: " + reply);

        /* Output:

        User: Hi, I'm from Tokyo, where are you from?
        Bot: https://oaidalleapiprodscus.blob.core.windows.net/private/...
        Img description: [An image of a globe with a pin dropped on a location in the middle of the ocean]

        User: Oh, wow. Not sure where that is, could you provide more details?
        Bot: https://oaidalleapiprodscus.blob.core.windows.net/private/...
        Img description: [An image of a map zooming in on the pin location, revealing a small island with a palm tree on it]

        */
    }

    public static async Task AzureOpenAIDallEAsync()
    {
        Console.WriteLine("========Azure OpenAI Dall-E 2 Image Generation ========");

        IKernel kernel = new KernelBuilder()
            .WithLogger(ConsoleLogger.Log)
            // Add your image generation service
            .WithAzureOpenAIImageGenerationService(Env.Var("AZURE_OPENAI_ENDPOINT"), Env.Var("AZURE_OPENAI_API_KEY"))
            // Add your chat completion service
            .WithAzureChatCompletionService("gpt-35-turbo", Env.Var("AZURE_OPENAI_ENDPOINT"), Env.Var("AZURE_OPENAI_API_KEY"))
            .Build();

        IImageGeneration dallE = kernel.GetService<IImageGeneration>();
        var imageDescription = "A cute baby sea otter";
        var image = await dallE.GenerateImageAsync(imageDescription, 256, 256);

        Console.WriteLine(imageDescription);
        Console.WriteLine("Image URL: " + image);

        /* Output:

        A cute baby sea otter
        Image URL: https://dalleproduse.blob.core.windows.net/private/images/....

        */

        Console.WriteLine("======== Chat with images ========");

        IChatCompletion chatGPT = kernel.GetService<IChatCompletion>();
        var chatHistory = (OpenAIChatHistory)chatGPT.CreateNewChat(
            "You're chatting with a user. Instead of replying directly to the user" +
            " provide the description of an image that expresses what you want to say." +
            " The user won't see your message, they will see only the image. The system " +
            " generates an image using your description, so it's important you describe the image with details.");

        var msg = "Hi, I'm from Tokyo, where are you from?";
        chatHistory.AddUserMessage(msg);
        Console.WriteLine("User: " + msg);

        string reply = await chatGPT.GenerateMessageAsync(chatHistory);
        chatHistory.AddAssistantMessage(reply);
        image = await dallE.GenerateImageAsync(reply, 256, 256);
        Console.WriteLine("Bot: " + image);
        Console.WriteLine("Img description: " + reply);

        msg = "Oh, wow. Not sure where that is, could you provide more details?";
        chatHistory.AddUserMessage(msg);
        Console.WriteLine("User: " + msg);

        reply = await chatGPT.GenerateMessageAsync(chatHistory);
        chatHistory.AddAssistantMessage(reply);
        image = await dallE.GenerateImageAsync(reply, 256, 256);
        Console.WriteLine("Bot: " + image);
        Console.WriteLine("Img description: " + reply);

        /* Output:

        User: Hi, I'm from Tokyo, where are you from?
        Bot: https://dalleproduse.blob.core.windows.net/private/images/......
        Img description: [An image of a globe with a pin dropped on a location in the middle of the ocean]

        User: Oh, wow. Not sure where that is, could you provide more details?
        Bot: https://dalleproduse.blob.core.windows.net/private/images/......
        Img description: [An image of a map zooming in on the pin location, revealing a small island with a palm tree on it]

        */
    }
}
