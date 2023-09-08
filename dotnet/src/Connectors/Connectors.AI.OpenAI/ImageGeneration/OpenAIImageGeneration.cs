// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.ImageGeneration;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.CustomClient;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ImageGeneration;
/// <summary>
/// A class for generating images using OpenAI's API.
/// </summary>
public class OpenAIImageGeneration : OpenAIClientBase, IImageGeneration
{
    /// <summary>
    /// OpenAI REST API endpoint
    /// </summary>
    private const string OpenAIEndpoint = "https://api.openai.com/v1/images/generations";

    /// <summary>
    /// Optional value for the OpenAI-Organization header.
    /// </summary>
    private readonly string? _organizationHeaderValue;

    /// <summary>
    /// Value for the authorization header.
    /// </summary>
    private readonly string _authorizationHeaderValue;

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIImageGeneration"/> class.
    /// </summary>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="organization">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public OpenAIImageGeneration(
        string apiKey,
        string? organization = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null
    ) : base(httpClient, loggerFactory)
    {
        Verify.NotNullOrWhiteSpace(apiKey);
        this._authorizationHeaderValue = $"Bearer {apiKey}";
        this._organizationHeaderValue = organization;
    }

    /// <summary>Adds headers to use for OpenAI HTTP requests.</summary>
    private protected override void AddRequestHeaders(HttpRequestMessage request)
    {
        base.AddRequestHeaders(request);

        request.Headers.Add("Authorization", this._authorizationHeaderValue);
        if (!string.IsNullOrEmpty(this._organizationHeaderValue))
        {
            request.Headers.Add("OpenAI-Organization", this._organizationHeaderValue);
        }
    }

    /// <inheritdoc/>
    public Task<string> GenerateImageAsync(string description, int width, int height, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(description);
        if (width != height || (width != 256 && width != 512 && width != 1024))
        {
            throw new ArgumentOutOfRangeException(nameof(width), width, "OpenAI can generate only square images of size 256x256, 512x512, or 1024x1024.");
        }

        return this.GenerateImageAsync(description, width, height, "url", x => x.Url, cancellationToken);
    }

    private async Task<string> GenerateImageAsync(
        string description,
        int width, int height,
        string format, Func<ImageGenerationResponse.Image, string> extractResponse,
        CancellationToken cancellationToken)
    {
        Debug.Assert(width == height);
        Debug.Assert(width is 256 or 512 or 1024);
        Debug.Assert(format is "url" or "b64_json");
        Debug.Assert(extractResponse is not null);

        var requestBody = Json.Serialize(new ImageGenerationRequest
        {
            Prompt = description,
            Size = $"{width}x{height}",
            Count = 1,
            Format = format,
        });

        var list = await this.ExecuteImageGenerationRequestAsync(OpenAIEndpoint, requestBody, extractResponse!, cancellationToken).ConfigureAwait(false);
        return list[0];
    }
}
