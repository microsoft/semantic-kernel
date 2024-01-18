// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.ImageToImage;
using Microsoft.SemanticKernel.Connectors.StableDiffusion;

// ReSharper disable once InconsistentNaming
public static class Example50_StableDiffusionImageToImage
{
    /// <summary>
    /// Show how to use Stable Diffusion's image to image model.
    /// </summary>
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Stable Diffusion - Image to image ========");

        string apiKey = TestConfiguration.StableDiffusion.ApiKey;

        if (apiKey is null)
        {
            Console.WriteLine("Stable Diffusion API key not found. Skipping example.");

            return;
        }

        var kernel = Kernel.CreateBuilder()
            .AddStableDiffusionImageToImage(apiKey)
            .Build();

        var imageToImageService = kernel.GetRequiredService<IImageToImageService>();

        // You can provide a PNG to modify from a URI, from a local path, or as an array of bytes
        byte[] output = await imageToImageService.GenerateModifiedImageAsync(new Uri("https://ccreleasetemplates.z21.web.core.windows.net/img2img.png"),
                                                                             "An art nouveau portrait", 1024, 1024, kernel);

        // Uncomment to write modified image to your computer's desktop
        //await File.WriteAllBytesAsync(Environment.ExpandEnvironmentVariables("%USERPROFILE%/Desktop/img2img-modded.png"), output);

        Console.WriteLine($"Modified image size is {output.Length}");
    }
}
