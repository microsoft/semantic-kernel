// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Buffers;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Numerics.Tensors;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using FastBertTokenizer;
using Microsoft.Extensions.Logging;
using Microsoft.ML.OnnxRuntime;
using Microsoft.SemanticKernel.Embeddings;
using IServiceCollection = Microsoft.Extensions.DependencyInjection.OnnxServiceCollectionExtensions;

namespace Microsoft.SemanticKernel.Connectors.Onnx;

#pragma warning disable CS0618 // Type or member is obsolete
#pragma warning disable CA2000 // Dispose objects before losing scope
#pragma warning disable CS1998 // Async method lacks 'await' operators and will run synchronously
#pragma warning disable VSTHRD002 // Avoid problematic synchronous waits
#pragma warning disable CS0419 // Ambiguous reference in cref attribute
/// <summary>
/// Provides a text embedding generation service using a BERT ONNX model.
/// </summary>
/// <remarks>
/// This service is obsolete and will be removed in a future version. Please use one of the extensions options below:
/// <list type="bullet">
/// <item><see cref="OnnxKernelBuilderExtensions.AddBertOnnxEmbeddingGenerator"/>.</item>
/// <item><see cref="IServiceCollection.AddBertOnnxEmbeddingGenerator" />.</item>
/// </list>
/// </remarks>
[Obsolete("Use AddBertOnnxEmbeddingGenerator extensions instead.")]
public sealed class BertOnnxTextEmbeddingGenerationService : ITextEmbeddingGenerationService, IDisposable
{
    /// <summary>Reusable options instance passed to OnnxSession.Run.</summary>
    private static readonly RunOptions s_runOptions = new();
    /// <summary>Reusable input name columns passed to OnnxSession.Run.</summary>
    private static readonly string[] s_inputNames = ["input_ids", "attention_mask", "token_type_ids"];

    /// <summary>The ONNX session instance associated with this service. This may be used concurrently.</summary>
    private readonly InferenceSession _onnxSession;
    /// <summary>The BertTokenizer instance associated with this service. This may be used concurrently as long as it's only used with methods to which destination state is passed.</summary>
    private readonly BertTokenizer _tokenizer;
    /// <summary>The user-configurable options associated with this instance.</summary>
    private readonly BertOnnxOptions _options;
    /// <summary>The number of dimensions in the resulting embeddings.</summary>
    private readonly int _dimensions;
    /// <summary>The token type IDs. Currently this always remains zero'd but is required for input to the model.</summary>
    private readonly long[] _tokenTypeIds;

    /// <summary>Prevent external instantiation. Stores supplied arguments into fields.</summary>
    private BertOnnxTextEmbeddingGenerationService(
        InferenceSession onnxSession,
        BertTokenizer tokenizer,
        int dimensions,
        BertOnnxOptions options)
    {
        this._onnxSession = onnxSession;
        this._tokenizer = tokenizer;
        this._dimensions = dimensions;
        this._options = options;
        this._tokenTypeIds = new long[options.MaximumTokens];
    }

    /// <summary>Creates a new instance of the <see cref="BertOnnxTextEmbeddingGenerationService"/> class.</summary>
    /// <param name="onnxModelPath">The path to the ONNX model file.</param>
    /// <param name="vocabPath">The path to the vocab file.</param>
    /// <param name="options">Options for the configuration of the model and service.</param>
    public static BertOnnxTextEmbeddingGenerationService Create(
        string onnxModelPath,
        string vocabPath,
        BertOnnxOptions? options = null)
    {
        Task<BertOnnxTextEmbeddingGenerationService> t = CreateAsync(onnxModelPath, vocabPath, options, async: false, cancellationToken: default);
        Debug.Assert(t.IsCompleted);
        return t.GetAwaiter().GetResult();
    }

    /// <summary>Creates a new instance of the <see cref="BertOnnxTextEmbeddingGenerationService"/> class.</summary>
    /// <param name="onnxModelStream">Stream containing the ONNX model.</param>
    /// <param name="vocabStream">Stream containing the vocab file.</param>
    /// <param name="options">Options for the configuration of the model and service.</param>
    public static BertOnnxTextEmbeddingGenerationService Create(
        Stream onnxModelStream,
        Stream vocabStream,
        BertOnnxOptions? options = null)
    {
        Task<BertOnnxTextEmbeddingGenerationService> t = CreateAsync(onnxModelStream, vocabStream, options, async: false, cancellationToken: default);
        Debug.Assert(t.IsCompleted);
        return t.GetAwaiter().GetResult();
    }

    /// <summary>Creates a new instance of the <see cref="BertOnnxTextEmbeddingGenerationService"/> class.</summary>
    /// <param name="onnxModelPath">The path to the ONNX model file.</param>
    /// <param name="vocabPath">The path to the vocab file.</param>
    /// <param name="options">Options for the configuration of the model and service.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public static Task<BertOnnxTextEmbeddingGenerationService> CreateAsync(
        string onnxModelPath,
        string vocabPath,
        BertOnnxOptions? options = null,
        CancellationToken cancellationToken = default) =>
        CreateAsync(onnxModelPath, vocabPath, options, async: true, cancellationToken: default);

    /// <summary>Creates a new instance of the <see cref="BertOnnxTextEmbeddingGenerationService"/> class.</summary>
    /// <param name="onnxModelStream">Stream containing the ONNX model.</param>
    /// <param name="vocabStream">Stream containing the vocab file.</param>
    /// <param name="options">Options for the configuration of the model and service.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public static Task<BertOnnxTextEmbeddingGenerationService> CreateAsync(
        Stream onnxModelStream,
        Stream vocabStream,
        BertOnnxOptions? options = null,
        CancellationToken cancellationToken = default) =>
        CreateAsync(onnxModelStream, vocabStream, options, async: true, cancellationToken: default);

    private static async Task<BertOnnxTextEmbeddingGenerationService> CreateAsync(
        string onnxModelPath,
        string vocabPath,
        BertOnnxOptions? options,
        bool async,
        CancellationToken cancellationToken)
    {
        Verify.NotNullOrWhiteSpace(onnxModelPath);
        Verify.NotNullOrWhiteSpace(vocabPath);

        using Stream onnxModelStream = new FileStream(onnxModelPath, FileMode.Open, FileAccess.Read, FileShare.Read, 1, async);
        using Stream vocabStream = new FileStream(vocabPath, FileMode.Open, FileAccess.Read, FileShare.Read, 1, async);

        return await CreateAsync(onnxModelStream, vocabStream, options, async, cancellationToken).ConfigureAwait(false);
    }

    private static async Task<BertOnnxTextEmbeddingGenerationService> CreateAsync(
        Stream onnxModelStream,
        Stream vocabStream,
        BertOnnxOptions? options,
        bool async,
        CancellationToken cancellationToken)
    {
        Verify.NotNull(onnxModelStream);
        Verify.NotNull(vocabStream);

        options ??= new();

        var modelBytes = new MemoryStream();
        if (async)
        {
            await onnxModelStream.CopyToAsync(modelBytes, 81920, cancellationToken).ConfigureAwait(false);
        }
        else
        {
            onnxModelStream.CopyTo(modelBytes);
        }

        var onnxSession = new InferenceSession(modelBytes.Length == modelBytes.GetBuffer().Length ? modelBytes.GetBuffer() : modelBytes.ToArray());
        int dimensions = onnxSession.OutputMetadata.First().Value.Dimensions.Last();

        var tokenizer = new BertTokenizer();
        using (StreamReader vocabReader = new(vocabStream, Encoding.UTF8, detectEncodingFromByteOrderMarks: true, bufferSize: 1024, leaveOpen: true))
        {
            if (async)
            {
                await tokenizer.LoadVocabularyAsync(vocabReader, convertInputToLowercase: !options.CaseSensitive, options.UnknownToken, options.ClsToken, options.SepToken, options.PadToken, options.UnicodeNormalization).ConfigureAwait(false);
            }
            else
            {
                tokenizer.LoadVocabulary(vocabReader, convertInputToLowercase: !options.CaseSensitive, options.UnknownToken, options.ClsToken, options.SepToken, options.PadToken, options.UnicodeNormalization);
            }
        }

        return new(onnxSession, tokenizer, dimensions, options);
    }

    /// <inheritdoc />
    public IReadOnlyDictionary<string, object?> Attributes { get; } = new Dictionary<string, object?>();

    /// <inheritdoc/>
    public void Dispose()
    {
        this._onnxSession.Dispose();
    }

    /// <inheritdoc/>
    public async Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(IList<string> data, Kernel? kernel = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(data);

        int inputCount = data.Count;
        if (inputCount == 0)
        {
            return Array.Empty<ReadOnlyMemory<float>>();
        }

        var shape = new long[] { 1L, 0 /*tokenCount*/ };
        var inputValues = new OrtValue[3];
        var results = new ReadOnlyMemory<float>[inputCount];

        OrtMemoryInfo info = OrtMemoryInfo.DefaultInstance;
        ILogger? logger = kernel?.LoggerFactory.CreateLogger(nameof(BertOnnxTextEmbeddingGenerationService));
        int maximumTokens = this._options.MaximumTokens;
        IReadOnlyList<string> outputNames = this._onnxSession.OutputNames;

        long[] scratch = ArrayPool<long>.Shared.Rent(this._options.MaximumTokens * 2);
        try
        {
            for (int i = 0; i < inputCount; i++)
            {
                string text = data[i];
                cancellationToken.ThrowIfCancellationRequested();

                int tokenCount = this._tokenizer.Encode(text, scratch.AsSpan(0, maximumTokens), scratch.AsSpan(maximumTokens, maximumTokens));
                shape[1] = tokenCount;

                using OrtValue inputIdsOrtValue = OrtValue.CreateTensorValueFromMemory(info, scratch.AsMemory(0, tokenCount), shape);
                using OrtValue attMaskOrtValue = OrtValue.CreateTensorValueFromMemory(info, scratch.AsMemory(maximumTokens, tokenCount), shape);
                using OrtValue typeIdsOrtValue = OrtValue.CreateTensorValueFromMemory(info, this._tokenTypeIds.AsMemory(0, tokenCount), shape);

                inputValues[0] = inputIdsOrtValue;
                inputValues[1] = attMaskOrtValue;
                inputValues[2] = typeIdsOrtValue;

                using IDisposableReadOnlyCollection<OrtValue> outputs = this._onnxSession.Run(s_runOptions, s_inputNames, inputValues, outputNames);

                results[i] = this.Pool(outputs[0].GetTensorDataAsSpan<float>());

                if (logger?.IsEnabled(LogLevel.Trace) is true)
                {
                    logger.LogTrace("Generated embedding for text: {Text}", text);
                }
            }

            return results;
        }
        finally
        {
            ArrayPool<long>.Shared.Return(scratch);
        }
    }

    private float[] Pool(ReadOnlySpan<float> modelOutput)
    {
        int dimensions = this._dimensions;
        int embeddings = Math.DivRem(modelOutput.Length, dimensions, out int leftover);
        if (leftover != 0)
        {
            throw new InvalidOperationException($"Expected output length {modelOutput.Length} to be a multiple of {dimensions} dimensions.");
        }

        float[] result = new float[dimensions];
        if (embeddings <= 1)
        {
            modelOutput.CopyTo(result);
        }
        else
        {
            switch (this._options.PoolingMode)
            {
                case EmbeddingPoolingMode.Mean or EmbeddingPoolingMode.MeanSquareRootTokensLength:
                    TensorPrimitives.Add(modelOutput.Slice(0, dimensions), modelOutput.Slice(dimensions, dimensions), result);
                    for (int pos = dimensions * 2; pos < modelOutput.Length; pos += dimensions)
                    {
                        TensorPrimitives.Add(result, modelOutput.Slice(pos, dimensions), result);
                    }

                    TensorPrimitives.Divide(
                        result,
                        this._options.PoolingMode is EmbeddingPoolingMode.Mean ? embeddings : MathF.Sqrt(embeddings),
                        result);
                    break;

                case EmbeddingPoolingMode.Max:
                    TensorPrimitives.Max(modelOutput.Slice(0, dimensions), modelOutput.Slice(dimensions, dimensions), result);
                    for (int pos = dimensions * 2; pos < modelOutput.Length; pos += dimensions)
                    {
                        TensorPrimitives.Max(result, modelOutput.Slice(pos, dimensions), result);
                    }
                    break;
            }
        }

        // If normalization has been requested, normalize the result.
        if (this._options.NormalizeEmbeddings)
        {
            TensorPrimitives.Divide(result, TensorPrimitives.Norm(result), result);
        }

        // Return the computed embedding vector.
        return result;
    }
}
