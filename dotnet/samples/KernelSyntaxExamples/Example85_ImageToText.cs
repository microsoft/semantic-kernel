// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.HuggingFace;
using Microsoft.SemanticKernel.ImageToText;
using Resources;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

/// <summary>
/// Represents a class that demonstrates audio processing functionality.
/// </summary>
public sealed class Example85_ImageToText : BaseTest
{
    private const string ImageToTextModel = "Salesforce/blip-image-captioning-base";
    private const string ImageFilePath = "cat.jpg";

    [Fact]
    public async Task ImageToTextAsync()
    {
        // Create a kernel with OpenAI text to audio service
        var kernel = Kernel.CreateBuilder()
            .AddHuggingFaceImageToText(
                model: ImageToTextModel,
                apiKey: TestConfiguration.HuggingFace.ApiKey)
            .Build();

        var imageToText = kernel.GetRequiredService<IImageToTextService>();

        // Set execution settings (optional)
        HuggingFacePromptExecutionSettings executionSettings = new()
        {
            MaxTokens = 500
        };

        // Read audio content from a file
        ReadOnlyMemory<byte> imageData = await EmbeddedResource.ReadAllAsync(ImageFilePath);
        ImageContent imageContent = new(new BinaryData(imageData, "image/jpeg"));

        // Convert audio to text
        var textContent = await imageToText.GetTextContentAsync(imageContent, executionSettings);

        // Output the transcribed text
        this.WriteLine(textContent.Text);
    }

    public Example85_ImageToText(ITestOutputHelper output) : base(output) { }
}
