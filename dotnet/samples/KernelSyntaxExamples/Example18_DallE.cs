// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.TextToImage;

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
        Console.WriteLine("======== OpenAI Dall-E 2 Text To Image ========");

        Kernel kernel = Kernel.CreateBuilder()
            // Add your text to image service
            .AddOpenAITextToImage(TestConfiguration.OpenAI.ApiKey)
            // Add your chat completion service 
            .AddOpenAIChatCompletion(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey)
            .Build();

        ITextToImageService dallE = kernel.GetRequiredService<ITextToImageService>();

        var imageDescription = "A cute baby sea otter";
        var image = await dallE.GenerateImageAsync(imageDescription, 256, 256);

        Console.WriteLine(imageDescription);
        Console.WriteLine("Image URL: " + image);

        /* Output:

        A cute baby sea otter
        Image URL: https://oaidalleapiprodscus.blob.core.windows.net/private/....

        */

        Console.WriteLine("======== Chat with images ========");

        IChatCompletionService chatGPT = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = new ChatHistory(
           "You're chatting with a user. Instead of replying directly to the user" +
           " provide the description of an image that expresses what you want to say." +
           " The user won't see your message, they will see only the image. The system " +
           " generates an image using your description, so it's important you describe the image with details.");

        var msg = "Hi, I'm from Tokyo, where are you from?";
        chatHistory.AddUserMessage(msg);
        Console.WriteLine("User: " + msg);

        var reply = await chatGPT.GetChatMessageContentAsync(chatHistory);
        chatHistory.Add(reply);
        image = await dallE.GenerateImageAsync(reply.Content!, 256, 256);
        Console.WriteLine("Bot: " + image);
        Console.WriteLine("Img description: " + reply);

        msg = "Oh, wow. Not sure where that is, could you provide more details?";
        chatHistory.AddUserMessage(msg);
        Console.WriteLine("User: " + msg);

        reply = await chatGPT.GetChatMessageContentAsync(chatHistory);
        chatHistory.Add(reply);
        image = await dallE.GenerateImageAsync(reply.Content!, 256, 256);
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
        Console.WriteLine("========Azure OpenAI Dall-E 2 Text To Image ========");

        Kernel kernel = Kernel.CreateBuilder()
            // Add your text to image service
            .AddAzureOpenAITextToImage(
                endpoint: TestConfiguration.AzureOpenAI.Endpoint,
                apiKey: TestConfiguration.AzureOpenAI.ApiKey,
                modelId: TestConfiguration.AzureOpenAI.ImageModelId)
            // Add your chat completion service
            .AddAzureOpenAIChatCompletion(
                deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
                endpoint: TestConfiguration.AzureOpenAI.Endpoint,
                apiKey: TestConfiguration.AzureOpenAI.ApiKey,
                modelId: TestConfiguration.AzureOpenAI.ChatModelId)
            .Build();

        ITextToImageService dallE = kernel.GetRequiredService<ITextToImageService>();
        var imageDescription = "A cute baby sea otter";
        var image = await dallE.GenerateImageAsync(imageDescription, 256, 256);

        Console.WriteLine(imageDescription);
        Console.WriteLine("Image URL: " + image);

        /* Output:

        A cute baby sea otter
        Image URL: https://dalleproduse.blob.core.windows.net/private/images/....

        */

        Console.WriteLine("======== Chat with images ========");

        IChatCompletionService chatGPT = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = new ChatHistory(
            "You're chatting with a user. Instead of replying directly to the user" +
            " provide the description of an image that expresses what you want to say." +
            " The user won't see your message, they will see only the image. The system " +
            " generates an image using your description, so it's important you describe the image with details.");

        var msg = "Hi, I'm from Tokyo, where are you from?";
        chatHistory.AddUserMessage(msg);
        Console.WriteLine("User: " + msg);

        var reply = await chatGPT.GetChatMessageContentAsync(chatHistory);
        chatHistory.Add(reply);
        image = await dallE.GenerateImageAsync(reply.Content!, 256, 256);
        Console.WriteLine("Bot: " + image);
        Console.WriteLine("Img description: " + reply);

        msg = "Oh, wow. Not sure where that is, could you provide more details?";
        chatHistory.AddUserMessage(msg);
        Console.WriteLine("User: " + msg);

        reply = await chatGPT.GetChatMessageContentAsync(chatHistory);
        chatHistory.Add(reply);
        image = await dallE.GenerateImageAsync(reply.Content!, 256, 256);
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
