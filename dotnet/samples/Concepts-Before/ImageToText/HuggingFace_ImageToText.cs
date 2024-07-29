// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.HuggingFace;
using Microsoft.SemanticKernel.ImageToText;
using Resources;

namespace ImageToText;

/// <summary>
/// Represents a class that demonstrates image-to-text functionality.
/// </summary>
public sealed class HuggingFace_ImageToText(ITestOutputHelper output) : BaseTest(output)
{
    private const string ImageToTextModel = "Salesforce/blip-image-captioning-base";
    private const string ImageFilePath = "test_image.jpg";

    [Fact]
    public async Task ImageToTextAsync()
    {
        // Create a kernel with HuggingFace image-to-text service
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

        // Read image content from a file
        ReadOnlyMemory<byte> imageData = await EmbeddedResource.ReadAllAsync(ImageFilePath);
        ImageContent imageContent = new(new BinaryData(imageData), "image/jpeg");

        // Convert image to text
        var textContent = await imageToText.GetTextContentAsync(imageContent, executionSettings);

        // Output image description
        Console.WriteLine(textContent.Text);
    }
}
