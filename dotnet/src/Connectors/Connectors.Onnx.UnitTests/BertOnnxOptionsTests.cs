// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text;
using Microsoft.SemanticKernel.Connectors.Onnx;
using Xunit;

namespace SemanticKernel.Connectors.Onnx.UnitTests;

public class BertOnnxTextEmbeddingGenerationServiceTests
{
    [Fact]
    public void VerifyOptionsDefaults()
    {
        var options = new BertOnnxOptions();
        Assert.False(options.CaseSensitive);
        Assert.Equal(512, options.MaximumTokens);
        Assert.Equal("[CLS]", options.ClsToken);
        Assert.Equal("[UNK]", options.UnknownToken);
        Assert.Equal("[SEP]", options.SepToken);
        Assert.Equal("[PAD]", options.PadToken);
        Assert.Equal(NormalizationForm.FormD, options.UnicodeNormalization);
        Assert.Equal(EmbeddingPoolingMode.Mean, options.PoolingMode);
        Assert.False(options.NormalizeEmbeddings);
    }

    [Fact]
    public void RoundtripOptionsProperties()
    {
        var options = new BertOnnxOptions()
        {
            CaseSensitive = true,
            MaximumTokens = 128,
            ClsToken = "<A>",
            UnknownToken = "<B>",
            SepToken = "<C>",
            PadToken = "<D>",
            UnicodeNormalization = NormalizationForm.FormKC,
            PoolingMode = EmbeddingPoolingMode.MeanSquareRootTokensLength,
            NormalizeEmbeddings = true,
        };

        Assert.True(options.CaseSensitive);
        Assert.Equal(128, options.MaximumTokens);
        Assert.Equal("<A>", options.ClsToken);
        Assert.Equal("<B>", options.UnknownToken);
        Assert.Equal("<C>", options.SepToken);
        Assert.Equal("<D>", options.PadToken);
        Assert.Equal(NormalizationForm.FormKC, options.UnicodeNormalization);
        Assert.Equal(EmbeddingPoolingMode.MeanSquareRootTokensLength, options.PoolingMode);
        Assert.True(options.NormalizeEmbeddings);
    }

    [Fact]
    public void ValidateInvalidOptionsPropertiesThrow()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => new BertOnnxOptions() { MaximumTokens = 0 });
        Assert.Throws<ArgumentOutOfRangeException>(() => new BertOnnxOptions() { MaximumTokens = -1 });

        Assert.Throws<ArgumentNullException>(() => new BertOnnxOptions() { ClsToken = null! });
        Assert.Throws<ArgumentException>(() => new BertOnnxOptions() { ClsToken = "   " });

        Assert.Throws<ArgumentNullException>(() => new BertOnnxOptions() { UnknownToken = null! });
        Assert.Throws<ArgumentException>(() => new BertOnnxOptions() { UnknownToken = "   " });

        Assert.Throws<ArgumentNullException>(() => new BertOnnxOptions() { SepToken = null! });
        Assert.Throws<ArgumentException>(() => new BertOnnxOptions() { SepToken = "   " });

        Assert.Throws<ArgumentNullException>(() => new BertOnnxOptions() { PadToken = null! });
        Assert.Throws<ArgumentException>(() => new BertOnnxOptions() { PadToken = "   " });

        Assert.Throws<ArgumentOutOfRangeException>(() => new BertOnnxOptions() { PoolingMode = (EmbeddingPoolingMode)4 });
    }
}
