// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Onnx;

/// <summary>
/// OnnxRuntimeGenAI Execution Settings.
/// </summary>
public sealed class OnnxRuntimeGenAIPromptExecutionSettings : PromptExecutionSettings
{
    /// <summary>
    /// Convert PromptExecutionSettings to OnnxRuntimeGenAIPromptExecutionSettings
    /// </summary>
    /// <param name="executionSettings"></param>
    /// <returns></returns>
    public static OnnxRuntimeGenAIPromptExecutionSettings FromExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        switch (executionSettings)
        {
            case OnnxRuntimeGenAIPromptExecutionSettings settings:
                return settings;
            default:
                return new OnnxRuntimeGenAIPromptExecutionSettings();
        }
    }

    private int _topK = 50;
    private float _topP = 0.9f;
    private float _temperature = 1;
    private float _repetitionPenalty = 1;
    private bool _pastPresentShareBuffer = false;
    private int _numReturnSequences = 1;
    private int _numBeams = 1;
    private int _noRepeatNgramSize = 0;
    private int _minLength = 0;
    private int _maxLength = 200;
    private float _lengthPenalty = 1;
    private bool _earlyStopping = true;
    private bool _doSample = false;
    private float _diversityPenalty = 0;

    [JsonPropertyName("top_k")]
    public int TopK
    {
        get { return this._topK; }
        set { this._topK = value; }
    }

    [JsonPropertyName("top_p")]
    public float TopP
    {
        get { return this._topP; }
        set { this._topP = value; }
    }

    [JsonPropertyName("temperature")]
    public float Temperature
    {
        get { return this._temperature; }
        set { this._temperature = value; }
    }

    [JsonPropertyName("repetition_penalty")]
    public float RepetitionPenalty
    {
        get { return this._repetitionPenalty; }
        set { this._repetitionPenalty = value; }
    }

    [JsonPropertyName("past_present_share_buffer")]
    public bool PastPresentShareBuffer
    {
        get { return this._pastPresentShareBuffer; }
        set { this._pastPresentShareBuffer = value; }
    }

    [JsonPropertyName("num_return_sequences")]
    public int NumReturnSequences
    {
        get { return this._numReturnSequences; }
        set { this._numReturnSequences = value; }
    }

    [JsonPropertyName("num_beams")]
    public int NumBeams
    {
        get { return this._numBeams; }
        set { this._numBeams = value; }
    }

    [JsonPropertyName("no_repeat_ngram_size")]
    public int NoRepeatNgramSize
    {
        get { return this._noRepeatNgramSize; }
        set { this._noRepeatNgramSize = value; }
    }

    [JsonPropertyName("min_length")]
    public int MinLength
    {
        get { return this._minLength; }
        set { this._minLength = value; }
    }

    [JsonPropertyName("max_length")]
    public int MaxLength
    {
        get { return this._maxLength; }
        set { this._maxLength = value; }
    }

    [JsonPropertyName("length_penalty")]
    public float LengthPenalty
    {
        get { return this._lengthPenalty; }
        set { this._lengthPenalty = value; }
    }

    [JsonPropertyName("diversity_penalty")]
    public float DiversityPenalty
    {
        get { return this._diversityPenalty; }
        set { this._diversityPenalty = value; }
    }

    [JsonPropertyName("early_stopping")]
    public bool EarlyStopping
    {
        get { return this._earlyStopping; }
        set { this._earlyStopping = value; }
    }

    [JsonPropertyName("do_sample")]
    public bool DoSample
    {
        get { return this._doSample; }
        set { this._doSample = value; }
    }
}
