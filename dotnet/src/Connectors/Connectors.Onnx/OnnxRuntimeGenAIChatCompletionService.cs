﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.ML.OnnxRuntimeGenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.Onnx;

/// <summary>
/// Represents a chat completion service using OnnxRuntimeGenAI.
/// </summary>
public sealed class OnnxRuntimeGenAIChatCompletionService : IChatCompletionService, IDisposable
{
    private readonly string _modelId;
    private readonly string _modelPath;
    private Model? _model;
    private Tokenizer? _tokenizer;

    private Dictionary<string, object?> AttributesInternal { get; } = new();

    /// <summary>
    /// Initializes a new instance of the OnnxRuntimeGenAIChatCompletionService class.
    /// </summary>
    /// <param name="modelId">The name of the model.</param>
    /// <param name="modelPath">The generative AI ONNX model path for the chat completion service.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public OnnxRuntimeGenAIChatCompletionService(
        string modelId,
        string modelPath,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(modelPath);

        this._modelId = modelId;
        this._modelPath = modelPath;

        this.AttributesInternal.Add(AIServiceExtensions.ModelIdKey, this._modelId);
    }

    /// <inheritdoc />
    public IReadOnlyDictionary<string, object?> Attributes => this.AttributesInternal;

    /// <inheritdoc />
    public async Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
    {
        var result = new StringBuilder();

        await foreach (var content in this.RunInferenceAsync(chatHistory, executionSettings, cancellationToken).ConfigureAwait(false))
        {
            result.Append(content);
        }

        return new List<ChatMessageContent>
        {
            new(
                role: AuthorRole.Assistant,
                modelId: this._modelId,
                content: result.ToString())
        };
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (var content in this.RunInferenceAsync(chatHistory, executionSettings, cancellationToken).ConfigureAwait(false))
        {
            yield return new StreamingChatMessageContent(AuthorRole.Assistant, content, modelId: this._modelId);
        }
    }

    private async IAsyncEnumerable<string> RunInferenceAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        OnnxRuntimeGenAIPromptExecutionSettings onnxPromptExecutionSettings = OnnxRuntimeGenAIPromptExecutionSettings.FromExecutionSettings(executionSettings);

        var prompt = this.GetPrompt(chatHistory, onnxPromptExecutionSettings);
        var tokens = this.GetTokenizer().Encode(prompt);

        using var generatorParams = new GeneratorParams(this.GetModel());
        this.UpdateGeneratorParamsFromPromptExecutionSettings(generatorParams, onnxPromptExecutionSettings);
        generatorParams.SetInputSequences(tokens);

        using var generator = new Generator(this.GetModel(), generatorParams);

        bool removeNextTokenStartingWithSpace = true;
        while (!generator.IsDone())
        {
            cancellationToken.ThrowIfCancellationRequested();

            yield return await Task.Run(() =>
            {
                generator.ComputeLogits();
                generator.GenerateNextToken();

                var outputTokens = generator.GetSequence(0);
                var newToken = outputTokens.Slice(outputTokens.Length - 1, 1);
                string output = this.GetTokenizer().Decode(newToken);

                if (removeNextTokenStartingWithSpace && output[0] == ' ')
                {
                    removeNextTokenStartingWithSpace = false;
                    output = output.TrimStart();
                }

                return output;
            }, cancellationToken).ConfigureAwait(false);
        }
    }

    private Model GetModel() => this._model ??= new Model(this._modelPath);

    private Tokenizer GetTokenizer() => this._tokenizer ??= new Tokenizer(this.GetModel());

    private string GetPrompt(ChatHistory chatHistory, OnnxRuntimeGenAIPromptExecutionSettings onnxRuntimeGenAIPromptExecutionSettings)
    {
        var promptBuilder = new StringBuilder();
        foreach (var message in chatHistory)
        {
            promptBuilder.Append($"<|{message.Role}|>\n{message.Content}");
        }
        promptBuilder.Append("<|end|>\n<|assistant|>");

        return promptBuilder.ToString();
    }

    private void UpdateGeneratorParamsFromPromptExecutionSettings(GeneratorParams generatorParams, OnnxRuntimeGenAIPromptExecutionSettings onnxRuntimeGenAIPromptExecutionSettings)
    {
        if (onnxRuntimeGenAIPromptExecutionSettings.TopP.HasValue)
        {
            generatorParams.SetSearchOption("top_p", onnxRuntimeGenAIPromptExecutionSettings.TopP.Value);
        }
        if (onnxRuntimeGenAIPromptExecutionSettings.TopK.HasValue)
        {
            generatorParams.SetSearchOption("top_k", onnxRuntimeGenAIPromptExecutionSettings.TopK.Value);
        }
        if (onnxRuntimeGenAIPromptExecutionSettings.Temperature.HasValue)
        {
            generatorParams.SetSearchOption("temperature", onnxRuntimeGenAIPromptExecutionSettings.Temperature.Value);
        }
        if (onnxRuntimeGenAIPromptExecutionSettings.RepetitionPenalty.HasValue)
        {
            generatorParams.SetSearchOption("repetition_penalty", onnxRuntimeGenAIPromptExecutionSettings.RepetitionPenalty.Value);
        }
        if (onnxRuntimeGenAIPromptExecutionSettings.PastPresentShareBuffer.HasValue)
        {
            generatorParams.SetSearchOption("past_present_share_buffer", onnxRuntimeGenAIPromptExecutionSettings.PastPresentShareBuffer.Value);
        }
        if (onnxRuntimeGenAIPromptExecutionSettings.NumReturnSequences.HasValue)
        {
            generatorParams.SetSearchOption("num_return_sequences", onnxRuntimeGenAIPromptExecutionSettings.NumReturnSequences.Value);
        }
        if (onnxRuntimeGenAIPromptExecutionSettings.NoRepeatNgramSize.HasValue)
        {
            generatorParams.SetSearchOption("no_repeat_ngram_size", onnxRuntimeGenAIPromptExecutionSettings.NoRepeatNgramSize.Value);
        }
        if (onnxRuntimeGenAIPromptExecutionSettings.MinTokens.HasValue)
        {
            generatorParams.SetSearchOption("min_length", onnxRuntimeGenAIPromptExecutionSettings.MinTokens.Value);
        }
        if (onnxRuntimeGenAIPromptExecutionSettings.MaxTokens.HasValue)
        {
            generatorParams.SetSearchOption("max_length", onnxRuntimeGenAIPromptExecutionSettings.MaxTokens.Value);
        }
        if (onnxRuntimeGenAIPromptExecutionSettings.LengthPenalty.HasValue)
        {
            generatorParams.SetSearchOption("length_penalty", onnxRuntimeGenAIPromptExecutionSettings.LengthPenalty.Value);
        }
        if (onnxRuntimeGenAIPromptExecutionSettings.EarlyStopping.HasValue)
        {
            generatorParams.SetSearchOption("early_stopping", onnxRuntimeGenAIPromptExecutionSettings.EarlyStopping.Value);
        }
        if (onnxRuntimeGenAIPromptExecutionSettings.DoSample.HasValue)
        {
            generatorParams.SetSearchOption("do_sample", onnxRuntimeGenAIPromptExecutionSettings.DoSample.Value);
        }
        if (onnxRuntimeGenAIPromptExecutionSettings.DiversityPenalty.HasValue)
        {
            generatorParams.SetSearchOption("diversity_penalty", onnxRuntimeGenAIPromptExecutionSettings.DiversityPenalty.Value);
        }
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        this._tokenizer?.Dispose();
        this._model?.Dispose();
    }
}
