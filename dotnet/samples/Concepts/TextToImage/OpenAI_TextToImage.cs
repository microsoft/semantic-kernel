// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Http.Resilience;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.TextToImage;

namespace TextToImage;

// The following example shows how to use Semantic Kernel with OpenAI DALL-E 2 to create images
public class OpenAI_TextToImage(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task ChatDallE2Async()
    {
        Console.WriteLine("======== OpenAI DALL-E 2 Text To Image ========");

        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAITextToImage(TestConfiguration.OpenAI.ApiKey) // Add your text to image service
            .AddOpenAIChatCompletion(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey) // Add your chat completion service
            .Build();

        ITextToImageService dallE = kernel.GetRequiredService<ITextToImageService>();

        var imageDescription = "A cute baby sea otter";
        var images = await dallE.GetImageContentsAsync(imageDescription, new OpenAITextToImageExecutionSettings { Size = (256, 256) });
        var image = images[0].Uri!.ToString();
        Console.WriteLine(imageDescription);
        Console.WriteLine("Image URL: " + image);

        /* Output:

        A cute baby sea otter
        Image URL: https://oaidalleapiprodscus.blob.core.windows.net/private/....

        */

        Console.WriteLine("======== Chat with images ========");

        var chatGPT = kernel.GetRequiredService<IChatCompletionService>();
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
        images = await dallE.GetImageContentsAsync(reply.Content!, new OpenAITextToImageExecutionSettings { Size = (256, 256) });
        image = images[0].Uri!.ToString();
        Console.WriteLine("Bot: " + image);
        Console.WriteLine("Img description: " + reply);

        msg = "Oh, wow. Not sure where that is, could you provide more details?";
        chatHistory.AddUserMessage(msg);
        Console.WriteLine("User: " + msg);

        reply = await chatGPT.GetChatMessageContentAsync(chatHistory);
        chatHistory.Add(reply);
        images = await dallE.GetImageContentsAsync(reply.Content!, new OpenAITextToImageExecutionSettings { Size = (256, 256) });
        image = images[0].Uri!.ToString();
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

    [Fact]
    public async Task SimpleDallE3ImageUriAsync()
    {
        var builder = Kernel.CreateBuilder()
            .AddOpenAITextToImage( // Add your text to image service
                modelId: "dall-e-3",
                apiKey: TestConfiguration.OpenAI.ApiKey);

        var kernel = builder.Build();
        var service = kernel.GetRequiredService<ITextToImageService>();

        var generatedImages = await service.GetImageContentsAsync(
            new TextContent("A cute baby sea otter"),
            new OpenAITextToImageExecutionSettings { Size = (Width: 1792, Height: 1024) });

        this.Output.WriteLine(generatedImages[0].Uri!.ToString());
    }

    [Fact]
    public async Task SimpleDallE3ImageBinaryAsync()
    {
        var builder = Kernel.CreateBuilder()
            .AddOpenAITextToImage( // Add your text to image service
                modelId: "dall-e-3",
                apiKey: TestConfiguration.OpenAI.ApiKey);

        var kernel = builder.Build();
        var service = kernel.GetRequiredService<ITextToImageService>();

        var generatedImages = await service.GetImageContentsAsync(new TextContent("A cute baby sea otter"),
            new OpenAITextToImageExecutionSettings
            {
                Size = (Width: 1024, Height: 1024),
                // Response Format also accepts the OpenAI.Images.GeneratedImageFormat type. 
                ResponseFormat = "bytes",
            });

        this.Output.WriteLine($"Generated Image Bytes: {generatedImages[0].Data!.Value.Length}");
        this.Output.WriteLine($"Generated Image DataUri: {generatedImages[0].DataUri}");
    }

    [Fact]
    public async Task ChatDallE3Async()
    {
        Console.WriteLine("======== OpenAI DALL-E 3 Text To Image ========");

        var builder = Kernel.CreateBuilder()
            .AddOpenAITextToImage( // Add your text to image service
                modelId: "dall-e-3",
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .AddOpenAIChatCompletion( // Add your chat completion service
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey);

        builder.Services.ConfigureHttpClientDefaults(c =>
        {
            // Use a standard resiliency policy, augmented to retry 5 times
            c.AddStandardResilienceHandler().Configure(o =>
            {
                o.Retry.MaxRetryAttempts = 5;
                o.TotalRequestTimeout.Timeout = TimeSpan.FromSeconds(120);
            });
        });

        var kernel = builder.Build();

        ITextToImageService dallE = kernel.GetRequiredService<ITextToImageService>();
        var imageDescription = "A cute baby sea otter";
        var images = await dallE.GetImageContentsAsync(imageDescription, new OpenAITextToImageExecutionSettings { Size = (1024, 1024) });

        Console.WriteLine(imageDescription);
        Console.WriteLine("Image URL: " + images[0].Uri!);

        /* Output:

        A cute baby sea otter
        Image URL: https://oaidalleapiprodscus.blob.core.windows.net/private/org-/....

        */

        Console.WriteLine("======== Chat with images ========");

        var chatGPT = kernel.GetRequiredService<IChatCompletionService>();
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
        images = await dallE.GetImageContentsAsync(reply.Content!, new OpenAITextToImageExecutionSettings { Size = (1024, 1024) });
        var image = images[0].Uri!.ToString();
        Console.WriteLine("Bot: " + image);
        Console.WriteLine("Img description: " + reply);

        msg = "Oh, wow. Not sure where that is, could you provide more details?";
        chatHistory.AddUserMessage(msg);
        Console.WriteLine("User: " + msg);

        reply = await chatGPT.GetChatMessageContentAsync(chatHistory);
        chatHistory.Add(reply);
        images = await dallE.GetImageContentsAsync(reply.Content!, new OpenAITextToImageExecutionSettings { Size = (1024, 1024) });
        image = images[0].Uri!.ToString();
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
