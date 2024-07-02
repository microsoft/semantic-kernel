// Copyright (c) Microsoft. All rights reserved.

using Amazon.BedrockRuntime.Model;
using Microsoft.SemanticKernel;
namespace Connectors.Amazon.Core.Responses;

public interface IChatCompletionResponse
{
    public ConverseOutput Output { get; set; }
    public string StopReason { get; set; }
    public TokenUsage Usage { get; set; }
    public ConverseMetrics Metrics { get; set; }
}
