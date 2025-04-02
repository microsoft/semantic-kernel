// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.HuggingFace;

/// <summary>
/// HuggingFace Execution Settings.
/// </summary>
[JsonNumberHandling(JsonNumberHandling.AllowReadingFromString)]
public sealed class HuggingFacePromptExecutionSettings : PromptExecutionSettings
{
    /// <summary>
    /// Gets the specialization for the HuggingFace execution settings.
    /// </summary>
    /// <param name="executionSettings">Generic prompt execution settings.</param>
    /// <returns>Specialized HuggingFace execution settings.</returns>
    public static HuggingFacePromptExecutionSettings FromExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        switch (executionSettings)
        {
            case null:
                return new HuggingFacePromptExecutionSettings();
            case HuggingFacePromptExecutionSettings settings:
                return settings;
        }

        var json = JsonSerializer.Serialize(executionSettings);
        var huggingFacePromptExecutionSettings = JsonSerializer.Deserialize<HuggingFacePromptExecutionSettings>(json, JsonOptionsCache.ReadPermissive);

        return huggingFacePromptExecutionSettings!;
    }

    /// <summary>
    /// (Default: 1.0). Float (0.0-100.0). The temperature of the sampling operation. 1 means regular sampling,
    /// 0 means always take the highest score, 100.0 is getting closer to uniform probability.
    /// </summary>
    [JsonPropertyName("temperature")]
    public float Temperature
    {
        get => this._temperature;

        set
        {
            this.ThrowIfFrozen();
            this._temperature = value;
        }
    }

    /// <summary>
    /// (Default: None). Integer to define the top tokens considered within the sample operation to create new text.
    /// </summary>
    /// <remarks>
    /// This may not be supported by all models/inference API.
    /// </remarks>
    [JsonPropertyName("top_k")]
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
    /// The maximum number of tokens to generate in the completion.
    /// </summary>
    [JsonPropertyName("max_tokens")]
    public int? MaxTokens
    {
        get => this._maxTokens;

        set
        {
            this.ThrowIfFrozen();
            this._maxTokens = value;
        }
    }

    /// <summary>
    /// Int (0-250). The amount of new tokens to be generated, this does not include the input length it is a estimate of the size of generated text you want.
    /// Each new tokens slows down the request, so look for balance between response times and length of text generated.
    /// </summary>
    [JsonPropertyName("max_new_tokens")]
    public int? MaxNewTokens
    {
        get => this._maxNewTokens;

        set
        {
            this.ThrowIfFrozen();
            this._maxNewTokens = value;
        }
    }

    /// <summary>
    /// (Default: None). Float (0-120.0). The amount of time in seconds that the query should take maximum.
    /// Network can cause some overhead so it will be a soft limit. Use that in combination with max_new_tokens for best results.
    /// </summary>
    /// <remarks>
    /// This may not be supported by all models/inference API.
    /// </remarks>
    [JsonPropertyName("max_time")]
    public float? MaxTime
    {
        get => this._maxTime;

        set
        {
            this.ThrowIfFrozen();
            this._maxTime = value;
        }
    }

    /// <summary>
    /// (Default: None). Float to define the tokens that are within the sample operation of text generation.
    /// Add tokens in the sample for more probable to least probable until the sum of the probabilities is greater than top_p.
    /// </summary>
    [JsonPropertyName("top_p")]
    public float? TopP
    {
        get => this._topP;

        set
        {
            this.ThrowIfFrozen();
            this._topP = value;
        }
    }

    /// <summary>
    /// (Default: None). Float (0.0-100.0). The more a token is used within generation the more
    /// it is penalized to not be picked in successive generation passes.
    /// </summary>
    /// <remarks>
    /// This may not be supported by all models/inference API.
    /// </remarks>
    [JsonPropertyName("repetition_penalty")]
    public float? RepetitionPenalty
    {
        get => this._repetitionPenalty;

        set
        {
            this.ThrowIfFrozen();
            this._repetitionPenalty = value;
        }
    }

    /// <summary>
    /// (Default: true). Boolean. There is a cache layer on the inference API to speedup requests we have already seen.
    /// Most models can use those results as is as models are deterministic (meaning the results will be the same anyway).
    /// However if you use a non deterministic model, you can set this parameter to prevent the caching mechanism from being used
    /// resulting in a real new query.
    /// </summary>
    /// <remarks>
    /// This may not be supported by all models/inference API.
    /// </remarks>
    [JsonPropertyName("use_cache")]
    public bool UseCache
    {
        get => this._useCache;

        set
        {
            this.ThrowIfFrozen();
            this._useCache = value;
        }
    }

    /// <summary>
    /// (Default: false) Boolean. If the model is not ready, wait for it instead of receiving 503.
    /// It limits the number of requests required to get your inference done.
    /// It is advised to only set this flag to true after receiving a 503 error as it will limit hanging in your application to known places.
    /// </summary>
    /// <remarks>
    /// This may not be supported by all models/inference API.
    /// </remarks>
    [JsonPropertyName("wait_for_model")]
    [JsonConverter(typeof(BoolJsonConverter))]
    public bool WaitForModel
    {
        get => this._waitForModel;

        set
        {
            this.ThrowIfFrozen();
            this._waitForModel = value;
        }
    }

    /// <summary>
    /// (Default: 1). Integer. The number of proposition you want to be returned.
    /// </summary>
    /// <remarks>
    /// This may not be supported by all models/inference API.
    /// </remarks>
    [JsonPropertyName("results_per_prompt")]
    public int ResultsPerPrompt
    {
        get => this._resultsPerPrompt;

        set
        {
            this.ThrowIfFrozen();
            this._resultsPerPrompt = value;
        }
    }

    /// <summary>
    /// Number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in the text so far,
    /// increasing the model's likelihood to talk about new topics
    /// </summary>
    [JsonPropertyName("presence_penalty")]
    public float? PresencePenalty
    {
        get => this._presencePenalty;

        set
        {
            this.ThrowIfFrozen();
            this._presencePenalty = value;
        }
    }

    /// <summary>
    /// Whether to return log probabilities of the output tokens or not. If true, returns the log probabilities of each
    /// output token returned in the content of message.
    /// </summary>
    [JsonPropertyName("logprobs")]
    [JsonConverter(typeof(OptionalBoolJsonConverter))]
    public bool? LogProbs
    {
        get => this._logProbs;

        set
        {
            this.ThrowIfFrozen();
            this._logProbs = value;
        }
    }

    /// <summary>
    /// The seed to use for generating a similar output.
    /// </summary>
    [JsonPropertyName("seed")]
    public long? Seed
    {
        get => this._seed;

        set
        {
            this.ThrowIfFrozen();
            this._seed = value;
        }
    }

    /// <summary>
    /// Up to 4 sequences where the API will stop generating further tokens.
    /// </summary>
    [JsonPropertyName("stop")]
    public List<string>? Stop
    {
        get => this._stop;

        set
        {
            this.ThrowIfFrozen();
            this._stop = value;
        }
    }

    /// <summary>
    /// An integer between 0 and 5 specifying the number of most likely tokens to return at each token position, each with
    /// an associated log probability. logprobs must be set to true if this parameter is used.
    /// </summary>
    [JsonPropertyName("top_logprobs")]
    public int? TopLogProbs
    {
        get => this._topLogProbs;

        set
        {
            this.ThrowIfFrozen();
            this._topLogProbs = value;
        }
    }

    /// <summary>
    /// (Default: True). Bool. If set to False, the return results will not contain the original query making it easier for prompting.
    /// </summary>
    [JsonPropertyName("return_full_text")]
    [JsonConverter(typeof(OptionalBoolJsonConverter))]
    public bool? ReturnFullText
    {
        get => this._returnFullText;

        set
        {
            this.ThrowIfFrozen();
            this._returnFullText = value;
        }
    }

    /// <summary>
    /// (Optional: True). Bool. Whether or not to use sampling, use greedy decoding otherwise.
    /// </summary>
    [JsonPropertyName("do_sample")]
    [JsonConverter(typeof(OptionalBoolJsonConverter))]
    public bool? DoSample
    {
        get => this._doSample;

        set
        {
            this.ThrowIfFrozen();
            this._doSample = value;
        }
    }

    /// <summary>
    /// Show details of the generation. Including usage.
    /// </summary>
    [JsonPropertyName("details")]
    [JsonConverter(typeof(OptionalBoolJsonConverter))]
    public bool? Details
    {
        get => this._details;

        set
        {
            this.ThrowIfFrozen();
            this._details = value;
        }
    }

    /// <inheritdoc />
    public override PromptExecutionSettings Clone()
    {
        return new HuggingFacePromptExecutionSettings()
        {
            ModelId = this.ModelId,
            ExtensionData = this.ExtensionData is not null ? new Dictionary<string, object>(this.ExtensionData) : null,
            Temperature = this.Temperature,
            TopP = this.TopP,
            TopK = this.TopK,
            MaxTokens = this.MaxTokens,
            MaxNewTokens = this.MaxNewTokens,
            MaxTime = this.MaxTime,
            RepetitionPenalty = this.RepetitionPenalty,
            UseCache = this.UseCache,
            WaitForModel = this.WaitForModel,
            ResultsPerPrompt = this.ResultsPerPrompt,
            PresencePenalty = this.PresencePenalty,
            LogProbs = this.LogProbs,
            Seed = this.Seed,
            Stop = this.Stop is not null ? new List<string>(this.Stop) : null,
            TopLogProbs = this.TopLogProbs,
            ReturnFullText = this.ReturnFullText,
            DoSample = this.DoSample,
        };
    }

    private float? _presencePenalty;
    private bool? _logProbs;
    private long? _seed;
    private List<string>? _stop;
    private int? _topLogProbs;
    private int _resultsPerPrompt = 1;
    private float _temperature = 1;
    private float? _topP;
    private float? _repetitionPenalty;
    private int? _maxTokens;
    private int? _maxNewTokens;
    private float? _maxTime;
    private int? _topK;
    private bool _useCache = true;
    private bool _waitForModel = false;
    private bool? _details;
    private bool? _returnFullText;
    private bool? _doSample;
}
