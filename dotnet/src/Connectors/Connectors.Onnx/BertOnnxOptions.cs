// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text;

namespace Microsoft.SemanticKernel.Connectors.Onnx;

/// <summary>Provides an options bag used to configure <see cref="BertOnnxTextEmbeddingGenerationService"/>.</summary>
public sealed class BertOnnxOptions
{
    private int _maximumTokens = 512;
    private string _clsToken = "[CLS]";
    private string _unknownToken = "[UNK]";
    private string _sepToken = "[SEP]";
    private string _padToken = "[PAD]";
    private EmbeddingPoolingMode _poolingMode = EmbeddingPoolingMode.Mean;

    /// <summary>Gets or sets whether the vocabulary employed by the model is case-sensitive.</summary>
    public bool CaseSensitive { get; init; } = false;

    /// <summary>Gets or sets the maximum number of tokens to encode. Defaults to 512.</summary>
    public int MaximumTokens
    {
        get => this._maximumTokens;
        init
        {
            if (value < 1)
            {
                throw new ArgumentOutOfRangeException(nameof(this.MaximumTokens));
            }

            this._maximumTokens = value;
        }
    }

    /// <summary>Gets or sets the cls token. Defaults to "[CLS]".</summary>
    public string ClsToken
    {
        get => this._clsToken;
        init
        {
            Verify.NotNullOrWhiteSpace(value);
            this._clsToken = value;
        }
    }

    /// <summary>Gets or sets the unknown token. Defaults to "[UNK]".</summary>
    public string UnknownToken
    {
        get => this._unknownToken;
        init
        {
            Verify.NotNullOrWhiteSpace(value);
            this._unknownToken = value;
        }
    }

    /// <summary>Gets or sets the sep token. Defaults to "[SEP]".</summary>
    public string SepToken
    {
        get => this._sepToken;
        init
        {
            Verify.NotNullOrWhiteSpace(value);
            this._sepToken = value;
        }
    }

    /// <summary>Gets or sets the pad token. Defaults to "[PAD]".</summary>
    public string PadToken
    {
        get => this._padToken;
        init
        {
            Verify.NotNullOrWhiteSpace(value);
            this._padToken = value;
        }
    }

    /// <summary>Gets or sets the type of Unicode normalization to perform on input text. Defaults to <see cref="NormalizationForm.FormD"/>.</summary>
    public NormalizationForm UnicodeNormalization { get; init; } = NormalizationForm.FormD;

    /// <summary>Gets or sets the pooling mode to use when generating the fixed-length embedding result. Defaults to "mean".</summary>
    public EmbeddingPoolingMode PoolingMode
    {
        get => this._poolingMode;
        init
        {
            if (value is not (EmbeddingPoolingMode.Max or EmbeddingPoolingMode.Mean or EmbeddingPoolingMode.MeanSquareRootTokensLength))
            {
                throw new ArgumentOutOfRangeException(nameof(this.PoolingMode));
            }

            this._poolingMode = value;
        }
    }

    /// <summary>Gets or sets whether the resulting embedding vectors should be explicitly normalized. Defaults to false.</summary>
    /// <remarks>Normalized embeddings may be compared more efficiently, such as by using a dot product rather than cosine similarity.</remarks>
    public bool NormalizeEmbeddings { get; set; } = false;
}
