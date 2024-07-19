// Copyright (c) Microsoft. All rights reserved.

namespace Connectors.Amazon.Core.Requests;

/// <summary>
/// Request object for text generation, essentially the base parameters for an InvokeModel request with Bedrock API.
/// </summary>
public interface ITextGenerationRequest
{
    /// <summary>
    /// The prompt given to Bedrock model.
    /// </summary>
    string InputText { get; }
    /// <summary>
    /// Consider probabilities that equal or exceed this value. Lower value to ignore less probable options and decrease the diversity of responses.
    /// </summary>
    double? TopP { get; }
    /// <summary>
    /// Use a lower value to decrease randomness in responses.
    /// </summary>
    double? Temperature { get; }
    /// <summary>
    /// Specify the maximum number of tokens to generate in the response. Maximum token limits are strictly enforced by model.
    /// </summary>
    int? MaxTokens { get; }
    /// <summary>
    /// Specify a character sequence to indicate where the model should stop.
    /// </summary>
    IList<string>? StopSequences { get; }
}
