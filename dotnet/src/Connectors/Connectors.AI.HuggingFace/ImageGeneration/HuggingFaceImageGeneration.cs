// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.ImageGeneration;

namespace Microsoft.SemanticKernel.Connectors.AI.HuggingFace.ImageGeneration;

/// <summary>
/// HuggingFace image generation service.
/// </summary>
#pragma warning disable CA1001 // Types that own disposable fields should be disposable. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
public sealed class HuggingFaceImageGeneration : HuggingFaceClientBase, IImageGeneration
#pragma warning disable CA1001 // Types that own disposable fields should be disposable. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
{
    /// <summary>
    /// Initializes a new instance of the <see cref="HuggingFaceImageGeneration"/> class.
    /// </summary>
    /// <param name="endpoint">Endpoint for service API call.</param>
    /// <param name="model">Model to use for service API call.</param>
    public HuggingFaceImageGeneration(Uri endpoint, string model) : base(endpoint, model)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="HuggingFaceImageGeneration"/> class.
    /// </summary>
    /// <param name="model">The name of the model to use for text completion.</param>
    /// <param name="apiKey">The API key for accessing the Hugging Face service.</param>
    /// <param name="httpClient">The HTTP client to use for making API requests. If not specified, a default client will be used.</param>
    /// <param name="endpoint">The endpoint URL for the Hugging Face service.</param>
    public HuggingFaceImageGeneration(string model, string? apiKey = null, HttpClient? httpClient = null, string? endpoint = null) : base(model, apiKey, httpClient, endpoint)
    {
    }

    /// <inheritdoc/>
    public async Task<string> GenerateImageAsync(string description, int width, int height, CancellationToken cancellationToken = default)
    {
        return await this.ExecuteGenerateImageRequestAsync(description, cancellationToken).ConfigureAwait(false);
    }

    #region private ================================================================================

    /// <summary>
    /// Performs HTTP request to given endpoint for image generation.
    /// </summary>
    /// <param name="description">Description of image to generate.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Generated image.</returns>
    private async Task<string> ExecuteGenerateImageRequestAsync(string description, CancellationToken cancellationToken = default)
    {
        var textToImageRequest = new TextToImageRequest
        {
            Input = description
        };

        using var response = await this.SendPostRequestAsync(textToImageRequest, cancellationToken).ConfigureAwait(false);

        using var memoryStream = new MemoryStream();
        await response.Content.CopyToAsync(memoryStream).ConfigureAwait(false);

        var imageData = memoryStream.ToArray();
        var result = Convert.ToBase64String(imageData);

        return result;
    }

    #endregion
}
