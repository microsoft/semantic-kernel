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
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.ML.OnnxRuntime;

namespace Microsoft.SemanticKernel.Connectors.Onnx;

#pragma warning disable CA2000 // Dispose objects before losing scope
#pragma warning disable CS1998 // Async method lacks 'await' operators and will run synchronously
#pragma warning disable VSTHRD002 // Avoid problematic synchronous waits

/// <summary>
/// Provides a text embedding generation service using a BERT ONNX model.
/// </summary>
public sealed class BertOnnxEmbeddingGenerator : IEmbeddingGenerator<string, Embedding<float>>
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
    private readonly ILoggerFactory _loggerFactory;

    /// <summary>Prevent external instantiation. Stores supplied arguments into fields.</summary>
    private BertOnnxEmbeddingGenerator(
        InferenceSession onnxSession,
        BertTokenizer tokenizer,
        int dimensions,
        BertOnnxOptions options,
        ILoggerFactory loggerFactory)
    {
        this._onnxSession = onnxSession;
        this._tokenizer = tokenizer;
        this._dimensions = dimensions;
        this._options = options;
        this._tokenTypeIds = new long[options.MaximumTokens];
        this._loggerFactory = loggerFactory;
    }

    /// <summary>Creates a new instance of the <see cref="BertOnnxTextEmbeddingGenerationService"/> class.</summary>
    /// <param name="onnxModelPath">The path to the ONNX model file.</param>
    /// <param name="vocabPath">The path to the vocab file.</param>
    /// <param name="options">Options for the configuration of the model and service.</param>
    /// <param name="loggerFactory">Logger factory to create loggers.</param>
    public static BertOnnxEmbeddingGenerator Create(
        string onnxModelPath,
        string vocabPath,
        BertOnnxOptions? options = null,
        ILoggerFactory? loggerFactory = null)
    {
        Task<BertOnnxEmbeddingGenerator> t = CreateAsync(onnxModelPath, vocabPath, options, async: false, loggerFactory: loggerFactory, cancellationToken: default);
        Debug.Assert(t.IsCompleted);
        return t.GetAwaiter().GetResult();
    }

    /// <summary>Creates a new instance of the <see cref="BertOnnxTextEmbeddingGenerationService"/> class.</summary>
    /// <param name="onnxModelStream">Stream containing the ONNX model.</param>
    /// <param name="vocabStream">Stream containing the vocab file.</param>
    /// <param name="options">Options for the configuration of the model and service.</param>
    /// <param name="loggerFactory">Logger factory to create loggers.</param>
    public static BertOnnxEmbeddingGenerator Create(
        Stream onnxModelStream,
        Stream vocabStream,
        BertOnnxOptions? options = null,
        ILoggerFactory? loggerFactory = null)
    {
        Task<BertOnnxEmbeddingGenerator> t = CreateAsync(onnxModelStream, vocabStream, options, async: false, loggerFactory: loggerFactory, cancellationToken: default);
        Debug.Assert(t.IsCompleted);
        return t.GetAwaiter().GetResult();
    }

    /// <summary>Creates a new instance of the <see cref="BertOnnxTextEmbeddingGenerationService"/> class.</summary>
    /// <param name="onnxModelPath">The path to the ONNX model file.</param>
    /// <param name="vocabPath">The path to the vocab file.</param>
    /// <param name="options">Options for the configuration of the model and service.</param>
    /// <param name="loggerFactory">Logger factory to create loggers.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public static Task<BertOnnxEmbeddingGenerator> CreateAsync(
        string onnxModelPath,
        string vocabPath,
        BertOnnxOptions? options = null,
        ILoggerFactory? loggerFactory = null,
        CancellationToken cancellationToken = default)
        => CreateAsync(onnxModelPath, vocabPath, options, async: true, loggerFactory: loggerFactory, cancellationToken: default);

    /// <summary>Creates a new instance of the <see cref="BertOnnxTextEmbeddingGenerationService"/> class.</summary>
    /// <param name="onnxModelStream">Stream containing the ONNX model.</param>
    /// <param name="vocabStream">Stream containing the vocab file.</param>
    /// <param name="options">Options for the configuration of the model and service.</param>
    /// <param name="loggerFactory">Logger factory to create loggers.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public static Task<BertOnnxEmbeddingGenerator> CreateAsync(
        Stream onnxModelStream,
        Stream vocabStream,
        BertOnnxOptions? options = null,
        ILoggerFactory? loggerFactory = null,
        CancellationToken cancellationToken = default)
        => CreateAsync(onnxModelStream, vocabStream, options, async: true, loggerFactory: loggerFactory ?? NullLoggerFactory.Instance, cancellationToken: default);

    private static async Task<BertOnnxEmbeddingGenerator> CreateAsync(
        string onnxModelPath,
        string vocabPath,
        BertOnnxOptions? options,
        bool async,
        ILoggerFactory? loggerFactory,
        CancellationToken cancellationToken)
    {
        Verify.NotNullOrWhiteSpace(onnxModelPath);
        Verify.NotNullOrWhiteSpace(vocabPath);

        using Stream onnxModelStream = new FileStream(onnxModelPath, FileMode.Open, FileAccess.Read, FileShare.Read, 1, async);
        using Stream vocabStream = new FileStream(vocabPath, FileMode.Open, FileAccess.Read, FileShare.Read, 1, async);

        return await CreateAsync(onnxModelStream, vocabStream, options, async, loggerFactory, cancellationToken).ConfigureAwait(false);
    }

    private static async Task<BertOnnxEmbeddingGenerator> CreateAsync(
        Stream onnxModelStream,
        Stream vocabStream,
        BertOnnxOptions? options,
        bool async,
        ILoggerFactory? loggerFactory,
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

        return new(onnxSession, tokenizer, dimensions, options, loggerFactory ?? NullLoggerFactory.Instance);
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        this._onnxSession.Dispose();
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

    /// <inheritdoc/>
    public async Task<GeneratedEmbeddings<Embedding<float>>> GenerateAsync(IEnumerable<string> values, EmbeddingGenerationOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(values);
        var data = values.ToArray();

        int inputCount = data.Length;
        if (inputCount == 0)
        {
            return [];
        }

        var shape = new long[] { 1L, 0 /*tokenCount*/ };
        var inputValues = new OrtValue[3];
        var results = new ReadOnlyMemory<float>[inputCount];

        OrtMemoryInfo info = OrtMemoryInfo.DefaultInstance;
        ILogger? logger = this._loggerFactory.CreateLogger(nameof(BertOnnxEmbeddingGenerator));
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

            return new(results.Select(e => new Embedding<float>(e)));
        }
        finally
        {
            ArrayPool<long>.Shared.Return(scratch);
        }
    }

    /// <inheritdoc/>
    public object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is null ? null :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }
}
