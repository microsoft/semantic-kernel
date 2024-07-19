// Copyright (c) Microsoft. All rights reserved.

using Amazon.BedrockRuntime.Model;

namespace Connectors.Amazon.Core.Responses;

/// <summary>
/// Chat completion response object, essentially a ConverseResponse object as outputted by the Bedrock Converse API call.
/// </summary>
public interface IChatCompletionResponse
{
    /// <summary>
    /// The output from a call to <a href="https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html">Converse</a>.
    /// </summary>
    public ConverseOutput Output { get; set; }
    /// <summary>
    /// Why the model stopped generating content.
    /// </summary>
    public string StopReason { get; set; }
    /// <summary>
    /// Information about the tokens passed to the model in the request, and the tokens generated in the response.
    /// </summary>
    public TokenUsage Usage { get; set; }
    /// <summary>
    /// Metrics for the call.
    /// </summary>
    public ConverseMetrics Metrics { get; set; }
}
