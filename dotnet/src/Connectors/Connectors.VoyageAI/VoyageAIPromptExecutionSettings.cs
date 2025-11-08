// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.VoyageAI;

/// <summary>
/// VoyageAI embedding prompt execution settings.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class VoyageAIEmbeddingPromptExecutionSettings : PromptExecutionSettings
{
    /// <summary>
    /// Type of input ('query' or 'document').
    /// Use 'query' for search queries and 'document' for content being searched.
    /// </summary>
    [JsonPropertyName("input_type")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? InputType
    {
        get => this._inputType;
        set
        {
            this.ThrowIfFrozen();
            this._inputType = value;
        }
    }

    /// <summary>
    /// Whether to truncate inputs that exceed the model's context length.
    /// Default is true.
    /// </summary>
    [JsonPropertyName("truncation")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? Truncation
    {
        get => this._truncation;
        set
        {
            this.ThrowIfFrozen();
            this._truncation = value;
        }
    }

    /// <summary>
    /// Desired embedding dimension (256, 512, 1024, or 2048).
    /// Allows dimension reduction from the model's default.
    /// </summary>
    [JsonPropertyName("output_dimension")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public int? OutputDimension
    {
        get => this._outputDimension;
        set
        {
            this.ThrowIfFrozen();
            this._outputDimension = value;
        }
    }

    /// <summary>
    /// Output data type ('float', 'int8', 'uint8', 'binary', or 'ubinary').
    /// Default is 'float'.
    /// </summary>
    [JsonPropertyName("output_dtype")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? OutputDtype
    {
        get => this._outputDtype;
        set
        {
            this.ThrowIfFrozen();
            this._outputDtype = value;
        }
    }

    /// <inheritdoc/>
    public override PromptExecutionSettings Clone()
    {
        return new VoyageAIEmbeddingPromptExecutionSettings()
        {
            ModelId = this.ModelId,
            ServiceId = this.ServiceId,
            InputType = this.InputType,
            Truncation = this.Truncation,
            OutputDimension = this.OutputDimension,
            OutputDtype = this.OutputDtype,
        };
    }

    /// <summary>
    /// Converts PromptExecutionSettings to VoyageAIEmbeddingPromptExecutionSettings.
    /// </summary>
    /// <param name="executionSettings">The source settings.</param>
    /// <returns>VoyageAI-specific execution settings.</returns>
    public static VoyageAIEmbeddingPromptExecutionSettings? FromExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        if (executionSettings is null)
        {
            return null;
        }

        if (executionSettings is VoyageAIEmbeddingPromptExecutionSettings settings)
        {
            return settings;
        }

        return new VoyageAIEmbeddingPromptExecutionSettings()
        {
            ModelId = executionSettings.ModelId,
            ServiceId = executionSettings.ServiceId,
        };
    }

    #region private

    private string? _inputType;
    private bool? _truncation = true;
    private int? _outputDimension;
    private string? _outputDtype;

    #endregion
}

/// <summary>
/// VoyageAI contextualized embedding prompt execution settings.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class VoyageAIContextualizedEmbeddingPromptExecutionSettings : PromptExecutionSettings
{
    /// <summary>
    /// Type of input ('query' or 'document').
    /// </summary>
    [JsonPropertyName("input_type")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? InputType
    {
        get => this._inputType;
        set
        {
            this.ThrowIfFrozen();
            this._inputType = value;
        }
    }

    /// <inheritdoc/>
    public override PromptExecutionSettings Clone()
    {
        return new VoyageAIContextualizedEmbeddingPromptExecutionSettings()
        {
            ModelId = this.ModelId,
            ServiceId = this.ServiceId,
            InputType = this.InputType,
        };
    }

    /// <summary>
    /// Converts PromptExecutionSettings to VoyageAIContextualizedEmbeddingPromptExecutionSettings.
    /// </summary>
    /// <param name="executionSettings">The source settings.</param>
    /// <returns>VoyageAI-specific execution settings.</returns>
    public static VoyageAIContextualizedEmbeddingPromptExecutionSettings? FromExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        if (executionSettings is null)
        {
            return null;
        }

        if (executionSettings is VoyageAIContextualizedEmbeddingPromptExecutionSettings settings)
        {
            return settings;
        }

        return new VoyageAIContextualizedEmbeddingPromptExecutionSettings()
        {
            ModelId = executionSettings.ModelId,
            ServiceId = executionSettings.ServiceId,
        };
    }

    #region private

    private string? _inputType;

    #endregion
}

/// <summary>
/// VoyageAI multimodal embedding prompt execution settings.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class VoyageAIMultimodalEmbeddingPromptExecutionSettings : PromptExecutionSettings
{
    /// <summary>
    /// Type of input ('query' or 'document').
    /// </summary>
    [JsonPropertyName("input_type")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? InputType
    {
        get => this._inputType;
        set
        {
            this.ThrowIfFrozen();
            this._inputType = value;
        }
    }

    /// <summary>
    /// Whether to truncate inputs that exceed the model's context length.
    /// Default is true.
    /// </summary>
    [JsonPropertyName("truncation")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? Truncation
    {
        get => this._truncation;
        set
        {
            this.ThrowIfFrozen();
            this._truncation = value;
        }
    }

    /// <inheritdoc/>
    public override PromptExecutionSettings Clone()
    {
        return new VoyageAIMultimodalEmbeddingPromptExecutionSettings()
        {
            ModelId = this.ModelId,
            ServiceId = this.ServiceId,
            InputType = this.InputType,
            Truncation = this.Truncation,
        };
    }

    /// <summary>
    /// Converts PromptExecutionSettings to VoyageAIMultimodalEmbeddingPromptExecutionSettings.
    /// </summary>
    /// <param name="executionSettings">The source settings.</param>
    /// <returns>VoyageAI-specific execution settings.</returns>
    public static VoyageAIMultimodalEmbeddingPromptExecutionSettings? FromExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        if (executionSettings is null)
        {
            return null;
        }

        if (executionSettings is VoyageAIMultimodalEmbeddingPromptExecutionSettings settings)
        {
            return settings;
        }

        return new VoyageAIMultimodalEmbeddingPromptExecutionSettings()
        {
            ModelId = executionSettings.ModelId,
            ServiceId = executionSettings.ServiceId,
        };
    }

    #region private

    private string? _inputType;
    private bool? _truncation = true;

    #endregion
}

/// <summary>
/// VoyageAI rerank prompt execution settings.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class VoyageAIRerankPromptExecutionSettings : PromptExecutionSettings
{
    /// <summary>
    /// Number of most relevant documents to return.
    /// </summary>
    [JsonPropertyName("top_k")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public int? TopK
    {
        get => this._topK;
        set
        {
            this.ThrowIfFrozen();
            this._topK = value;
        }
    }

    /// <summary>
    /// Whether to truncate inputs that exceed the model's context length.
    /// Default is true.
    /// </summary>
    [JsonPropertyName("truncation")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? Truncation
    {
        get => this._truncation;
        set
        {
            this.ThrowIfFrozen();
            this._truncation = value;
        }
    }

    /// <inheritdoc/>
    public override PromptExecutionSettings Clone()
    {
        return new VoyageAIRerankPromptExecutionSettings()
        {
            ModelId = this.ModelId,
            ServiceId = this.ServiceId,
            TopK = this.TopK,
            Truncation = this.Truncation,
        };
    }

    /// <summary>
    /// Converts PromptExecutionSettings to VoyageAIRerankPromptExecutionSettings.
    /// </summary>
    /// <param name="executionSettings">The source settings.</param>
    /// <returns>VoyageAI-specific execution settings.</returns>
    public static VoyageAIRerankPromptExecutionSettings? FromExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        if (executionSettings is null)
        {
            return null;
        }

        if (executionSettings is VoyageAIRerankPromptExecutionSettings settings)
        {
            return settings;
        }

        return new VoyageAIRerankPromptExecutionSettings()
        {
            ModelId = executionSettings.ModelId,
            ServiceId = executionSettings.ServiceId,
        };
    }

    #region private

    private int? _topK;
    private bool? _truncation = true;

    #endregion
}
