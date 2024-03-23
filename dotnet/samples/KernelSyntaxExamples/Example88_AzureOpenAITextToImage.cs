// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Azure;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.TextToImage;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

// The following example shows how to use Semantic Kernel with Azure OpenAI DALL-E 3 to create images
public class Example88_AzureOpenAITextToImage : BaseTest
{
    [Fact]
    public async Task AzureOpenAITextToImageAsync()
    {
        WriteLine("======== Azure OpenAI DALL-E Text To Image ========");

        string endpoint = TestConfiguration.AzureOpenAI.Endpoint;
        string apiKey = TestConfiguration.AzureOpenAI.ApiKey;
        string deploymentName = TestConfiguration.AzureOpenAI.ImageDeploymentName;

        // This sample creates a custom OpenAI client but you can also use the default client 
        // using this builder method: .AddAzureOpenAITextToImage(deploymentName, endpoint, apiKey)
        var openAIClient = new OpenAIClient(new Uri(endpoint), new AzureKeyCredential(apiKey));
        Kernel kernel = Kernel.CreateBuilder()
            .AddAzureOpenAITextToImage(deploymentName, openAIClient)
            .Build();

        ITextToImageService textToImage = kernel.GetRequiredService<ITextToImageService>();

        var imageDescription = "A cute cat playing the piano.";
        var image = await textToImage.GenerateImageAsync(imageDescription, 1024, 1024);

        WriteLine(imageDescription);
        WriteLine("Image URL: " + image);
    }

    public Example88_AzureOpenAITextToImage(ITestOutputHelper output) : base(output)
    {
    }
}
