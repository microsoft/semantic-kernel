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
    /// Initializes a new instance of the <see cref="OpenAITextToImageExecutionSettings"/> class.
    /// </summary>
    public OpenAITextToImageExecutionSettings()
    {
    }
    /// <summary>
    /// Optional width and height of the generated image.
    /// </summary>
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
    /// The quality of the image that will be generated. Defaults to "standard"
    /// "hd" or "high" creates images with finer details and greater consistency. This param is only supported for dall-e-3.
    /// </summary>
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
    /// The style of the generated images. Must be one of vivid or natural.
    /// Vivid causes the model to lean towards generating hyper-real and dramatic images.
    /// Natural causes the model to produce more natural, less hyper-real looking images.
    /// This param is only supported for dall-e-3.
    /// </summary>
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
    /// The format in which the generated images are returned.
    /// Can be a <see cref="GeneratedImageFormat"/> or a string where:
    /// <list type="bullet">
    /// <item>Url = "url" or "uri".</item>
    /// <item>Base64 = "b64_json" or "bytes".</item>
    /// </list>
    /// </summary>
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

        var openAIExecutionSettings = JsonSerializer.Deserialize<OpenAITextToImageExecutionSettings>(json, JsonOptionsCache.ReadPermissive);
        return openAIExecutionSettings!;
    }

    #region private ================================================================================

    private (int Width, int Height)? _size;
    private string? _quality;
    private string? _style;
    private object? _responseFormat;
    private string? _endUserId;

    #endregion
}
