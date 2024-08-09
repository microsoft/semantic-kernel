// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Text to image execution settings for an OpenAI image generation request.
/// </summary>
[JsonNumberHandling(JsonNumberHandling.AllowReadingFromString)]
public sealed class OpenAITextToImageExecutionSettings : PromptExecutionSettings
{
    private const int DefaultWidth = 1024;
    private const int DefaultHeight = 1024;

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAITextToImageExecutionSettings"/> class.
    /// </summary>
    public OpenAITextToImageExecutionSettings()
    {
        this.Width = DefaultWidth;
        this.Height = DefaultHeight;
    }
    /// <summary>
    /// Width of the generated image.
    /// </summary>
    public int Width
    {
        get => this._width;

        set
        {
            this.ThrowIfFrozen();
            this._width = value;
        }
    }

    /// <summary>
    /// The quality of the image that will be generated.
    /// `hd` creates images with finer details and greater consistency across the image.
    /// This param is only supported for dall-e-3.
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
    /// The number of images to generate. Must be between 1 and 10.
    /// For dall-e-3, only ImageCount = 1 is supported.
    /// </summary>
    public int? ImageCount
    {
        get => this._imageCount;

        set
        {
            this.ThrowIfFrozen();
            this._imageCount = value;
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
    /// Height of the generated image.
    /// </summary>
    public int Height
    {
        get => this._height;

        set
        {
            this.ThrowIfFrozen();
            this._height = value;
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
            Width = this.Width,
            Height = this.Height,
        };
    }

    /// <summary>
    /// Create a new settings object with the values from another settings object.
    /// </summary>
    /// <param name="executionSettings">Template configuration</param>
    /// <param name="defaultMaxTokens">Default max tokens</param>
    /// <returns>An instance of OpenAIPromptExecutionSettings</returns>
    public static OpenAITextToImageExecutionSettings FromExecutionSettings(PromptExecutionSettings? executionSettings, int? defaultMaxTokens = null)
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

    private int _width;
    private int _height;
    private int? _imageCount;
    private string? _quality;
    private string? _style;

    #endregion
}
