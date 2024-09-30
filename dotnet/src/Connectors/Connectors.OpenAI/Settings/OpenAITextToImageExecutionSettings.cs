// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;
using OpenAI.Images;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Text to image execution settings for an OpenAI image generation request.
/// </summary>
[JsonNumberHandling(JsonNumberHandling.AllowReadingFromString)]
public sealed class OpenAITextToImageExecutionSettings : PromptExecutionSettings
{
    /// <summary>
    /// Optional width and height of the generated image.
    /// </summary>
    /// <remarks>
    /// <list type="bullet">
    /// <item>Must be one of <c>256x256, 512x512, or 1024x1024</c> for <c>dall-e-2</c> model.</item>
    /// <item>Must be one of <c>1024x1024, 1792x1024, 1024x1792</c> for <c>dall-e-3</c> model.</item>
    /// </list>
    /// </remarks>
    public (int Width, int Height)? Size
    {
        get => this._size;

        set
        {
            this.ThrowIfFrozen();
            this._size = value;
        }
    }

    /// <summary>
    /// The quality of the image that will be generated.
    /// </summary>
    /// <remarks>
    /// Must be one of <c>standard</c> or <c>hd</c> or <c>high</c>.
    /// <list type="bullet">
    /// <item><c>standard</c>: creates images with standard quality. This is the default.</item>
    /// <item><c>hd</c> OR <c>high</c>: creates images with finer details and greater consistency.</item>
    /// </list>
    /// This param is only supported for <c>dall-e-3</c> model.
    /// </remarks>
    [JsonPropertyName("quality")]
    public string? Quality
    {
        get => this._quality;

        set
        {
            this.ThrowIfFrozen();
            this._quality = value;
        }
    }

    /// <summary>
    /// The style of the generated images.
    /// </summary>
    /// <remarks>
    /// Must be one of <c>vivid</c> or <c>natural</c>.
    /// <list type="bullet">
    /// <item><c>vivid</c>: causes the model to lean towards generating hyper-real and dramatic images.</item>
    /// <item><c>natural</c>: causes the model to produce more natural, less hyper-real looking images.</item>
    /// </list>
    /// This param is only supported for <c>dall-e-3</c> model.
    /// </remarks>
    [JsonPropertyName("style")]
    public string? Style
    {
        get => this._style;

        set
        {
            this.ThrowIfFrozen();
            this._style = value;
        }
    }

    /// <summary>
    /// The format of the generated images.
    /// Can be a <see cref="GeneratedImageFormat"/> or a <c>string</c> where:
    /// <list type="bullet">
    /// <item><see cref="GeneratedImageFormat"/>: causes the model to generated in the provided format</item>
    /// <item><c>url</c> OR <c>uri</c>: causes the model to return an url for the generated images.</item>
    /// <item><c>b64_json</c> or <c>bytes</c>: causes the model to return in a Base64 format the content of the images.</item>
    /// </list>
    /// </summary>
    [JsonPropertyName("response_format")]
    public object? ResponseFormat
    {
        get => this._responseFormat;
        set
        {
            this.ThrowIfFrozen();
            this._responseFormat = value;
        }
    }

    /// <summary>
    /// A unique identifier representing your end-user, which can help OpenAI to monitor and detect abuse.
    /// </summary>
    [JsonPropertyName("user")]
    public string? EndUserId
    {
        get => this._endUserId;
        set
        {
            this.ThrowIfFrozen();
            this._endUserId = value;
        }
    }

    /// <inheritdoc/>
    public override void Freeze()
    {
        if (this.IsFrozen)
        {
            return;
        }

        base.Freeze();
    }

    /// <inheritdoc/>
    public override PromptExecutionSettings Clone()
    {
        return new OpenAITextToImageExecutionSettings()
        {
            ModelId = this.ModelId,
            ExtensionData = this.ExtensionData is not null ? new Dictionary<string, object>(this.ExtensionData) : null,
            Size = this.Size
        };
    }

    /// <summary>
    /// Create a new settings object with the values from another settings object.
    /// </summary>
    /// <param name="executionSettings">Template configuration</param>
    /// <returns>An instance of OpenAIPromptExecutionSettings</returns>
    public static OpenAITextToImageExecutionSettings FromExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        if (executionSettings is null)
        {
            return new OpenAITextToImageExecutionSettings();
        }

        if (executionSettings is OpenAITextToImageExecutionSettings settings)
        {
            return settings;
        }

        var json = JsonSerializer.Serialize(executionSettings);
        var openAIExecutionSettings = JsonSerializer.Deserialize<OpenAITextToImageExecutionSettings>(json, JsonOptionsCache.ReadPermissive)!;
        if (openAIExecutionSettings.ExtensionData?.TryGetValue("width", out var width) ?? false)
        {
            openAIExecutionSettings.Width = ((JsonElement)width).GetInt32();
        }
        if (openAIExecutionSettings.ExtensionData?.TryGetValue("height", out var height) ?? false)
        {
            openAIExecutionSettings.Height = ((JsonElement)height).GetInt32();
        }

        return openAIExecutionSettings!;
    }

    #region private ================================================================================

    [JsonPropertyName("width")]
    internal int? Width
    {
        get => this.Size?.Width;
        set
        {
            if (!value.HasValue) { return; }
            this.Size = (value.Value, this.Size?.Height ?? 0);
        }
    }

    [JsonPropertyName("height")]
    internal int? Height
    {
        get => this.Size?.Height;
        set
        {
            if (!value.HasValue) { return; }
            this.Size = (this.Size?.Width ?? 0, value.Value);
        }
    }

    private (int Width, int Height)? _size;
    private string? _quality;
    private string? _style;
    private object? _responseFormat;
    private string? _endUserId;

    #endregion
}
