// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// Bedrock input-output service to build the request and response bodies as required by the given model.
/// </summary>
internal interface IBedrockTextGenerationIOService
{
    /// <summary>
    /// Builds InvokeModelRequest Body parameter to be serialized. Object itself dependent on model request parameter requirements.
    /// </summary>
    /// <param name="modelId">The model ID to be used as a request parameter.</param>
    /// <param name="prompt">The input prompt for text generation.</param>
    /// <param name="executionSettings">Optional prompt execution settings.</param>
    /// <returns>The invoke request body per model requirements for the InvokeAsync Bedrock runtime call.</returns>
    internal object GetInvokeModelRequestBody(string modelId, string prompt, PromptExecutionSettings? executionSettings = null);

    /// <summary>
    /// Extracts the test contents from the InvokeModelResponse as returned by the Bedrock API. Must be deserialized into the model's specific response object first.
    /// </summary>
    /// <param name="response">The InvokeModelResponse object returned from the InvokeAsync Bedrock call. </param>
    /// <returns>The list of TextContent objects for the Semantic Kernel output.</returns>
    internal IReadOnlyList<TextContent> GetInvokeResponseBody(InvokeModelResponse response);

    /// <summary>
    /// Converts the Json output from the streaming text generation into IEnumerable strings for output.
    /// </summary>
    /// <param name="chunk">The payloadPart bytes outputted from the streaming response.</param>
    /// <returns>An enumerable string.</returns>
    internal IEnumerable<string> GetTextStreamOutput(JsonNode chunk);
}
