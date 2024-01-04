// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.ImageToImage;

namespace Microsoft.SemanticKernel.Connectors.StableDiffusion.ImageToImage;

/// <summary>
/// Stable Diffusion implementation of image transformation (image to image service)
/// </summary>
public class StableDiffusionImageToImageService : IImageToImageService
{
    private const string EngineId = "stable-diffusion-xl-1024-v1-0"; // TODO: make this configurable
    private const string ImageToImageUri = $"https://api.stability.ai/v1/generation/{EngineId}/image-to-image";

    private readonly string _apiKey;
    private readonly HttpClient _httpClient;

    /// <summary>
    /// Constructor
    /// </summary>
    public StableDiffusionImageToImageService(string apiKey, HttpClient? httpClient = null)
    {
        this._apiKey = apiKey;
        this._httpClient = httpClient ?? new HttpClient();
        this._httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", this._apiKey);
        this._httpClient.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("image/png"));
    }

    /// <inheritdoc />
    public async Task<byte[]> GenerateModifiedImageAsync(byte[] inputFile, string prompt, int width, int height, Kernel? kernel = null, CancellationToken cancellationToken = default)
    {
        using var formData = new MultipartFormDataContent();
        using var stringContent = new StringContent(prompt);
        using var byteArrayContent = new ByteArrayContent(inputFile);

        formData.Add(stringContent, "text_prompts[0][text]");
        formData.Add(byteArrayContent, "init_image");

        HttpResponseMessage response = await this._httpClient.PostAsync(ImageToImageUri, formData, cancellationToken).ConfigureAwait(false);
        response.EnsureSuccessStatusCode();

        return await response.Content.ReadAsByteArrayAsync().ConfigureAwait(false);
    }
}
