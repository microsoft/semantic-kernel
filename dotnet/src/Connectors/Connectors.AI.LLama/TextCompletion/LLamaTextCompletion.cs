// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using LLama.Common;
using LLama;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.AI.LLama.TextCompletion;

/// <summary>
/// LLama text completion service.
/// </summary>
public sealed class LLamaTextCompletion : ITextCompletion, IDisposable
{
    /*
     modelPath, contextSize: 1024, seed: 1337, gpuLayerCount: 5)
     */
    private readonly string _modelPath;
    private readonly int _contextSize = 1024;
    private readonly int _seed = 1337;
    private readonly int _gpuLayerCount =5;
    List<string> _antiPrompts { set; get; }
    CompleteRequestSettings currentSetting { set; get; } 
    //ChatSession session { set; get; }
    InteractiveExecutor ex { set; get; }
    /// <summary>
    /// Initializes a new instance of the <see cref="LLamaTextCompletion"/> class.
    /// </summary>
    /// <param name="endpoint">Endpoint for service API call.</param>
    /// <param name="model">Model to use for service API call.</param>
    /// <param name="httpClientHandler">Instance of <see cref="HttpClientHandler"/> to setup specific scenarios.</param>
    [Obsolete("This constructor is deprecated and will be removed in one of the next SK SDK versions. Please use one of the alternative constructors.")]
    public LLamaTextCompletion(string modelPath)
    {
        Verify.NotNullOrWhiteSpace(modelPath);
        this._antiPrompts = null;
        this._modelPath = modelPath;
        // Initialize a chat session
        ex = new InteractiveExecutor(new LLamaModel(new ModelParams(this._modelPath, contextSize: this._contextSize, seed: this._seed, gpuLayerCount: this._gpuLayerCount)));
        //this.session = new ChatSession(ex);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="LLamaTextCompletion"/> class.
    /// Using default <see cref="HttpClientHandler"/> implementation.
    /// </summary>
    /// <param name="endpoint">Endpoint for service API call.</param>
    /// <param name="model">Model to use for service API call.</param>
    public LLamaTextCompletion(string modelPath, int contextSize, int seed,int gpuLayerCount, List<string> antiPrompts)
    {
        Verify.NotNullOrWhiteSpace(modelPath);
        this._antiPrompts = antiPrompts;
        this._modelPath = modelPath;
        this._contextSize = contextSize;
        this._seed = seed;
        this._gpuLayerCount = gpuLayerCount;
        // Initialize a chat session
        ex = new InteractiveExecutor(new LLamaModel(new ModelParams(this._modelPath, contextSize: this._contextSize, seed: this._seed, gpuLayerCount: this._gpuLayerCount)));
        //this.session = new ChatSession(ex);
    }

 

    /// <inheritdoc/>
    public async IAsyncEnumerable<ITextStreamingResult> GetStreamingCompletionsAsync(
        string text,
        CompleteRequestSettings requestSettings,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        foreach (var completion in await this.ExecuteGetCompletionsAsync(text, cancellationToken).ConfigureAwait(false))
        {
            yield return completion;
        }
    }

    /// <inheritdoc/>
    public async Task<IReadOnlyList<ITextResult>> GetCompletionsAsync(
        string text,
        CompleteRequestSettings requestSettings,
        CancellationToken cancellationToken = default)
    {
        this.currentSetting = requestSettings;
        return await this.ExecuteGetCompletionsAsync(text, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    [Obsolete("This method is deprecated and will be removed in one of the next SK SDK versions.")]
    public void Dispose()
    {
       
    }

    #region private ================================================================================

    private async Task<IReadOnlyList<ITextStreamingResult>> ExecuteGetCompletionsAsync(string text, CancellationToken cancellationToken = default)
    {
        try
        {
            var completionRequest = new TextCompletionRequest
            {
                Input = text
            };
            var content = string.Empty;
            await foreach (var output in ex.InferAsync(completionRequest.Input, new InferenceParams() { Temperature = (float)currentSetting?.Temperature, AntiPrompts = _antiPrompts }))
            {
                content += output;
            }
            /*
            foreach (var output in session.Chat(completionRequest.Input, new InferenceParams() { Temperature = (float)currentSetting?.Temperature, AntiPrompts = _antiPrompts }))
            {
                content += output;
            }*/

            List<TextCompletionResponse>? completionResponse = new List<TextCompletionResponse>() { new TextCompletionResponse() { Text = content } };

            if (completionResponse is null)
            {
                throw new AIException(AIException.ErrorCodes.InvalidResponseContent, "Unexpected response from model")
                {
                    Data = { { "ResponseData", content } },
                };
            }

            return completionResponse.ConvertAll(c => new TextCompletionStreamingResult(c));
        }
        catch (Exception e) when (e is not AIException && !e.IsCriticalException())
        {
            throw new AIException(
                AIException.ErrorCodes.UnknownError,
                $"Something went wrong: {e.Message}", e);
        }
    }

    

    #endregion
}
