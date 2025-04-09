// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// Bedrock input-output service to build the request and response bodies as required by the given model.
/// </summary>
internal interface IBedrockTextGenerationService
{
    /// <summary>
    /// Returns the specialized <see cref="InvokeModelRequest"/> instance for request.
    /// </summary>
    /// <param name="modelId">The model ID to be used as a request parameter.</param>
    /// <param name="prompt">The input prompt for text generation.</param>
    /// <param name="executionSettings">Optional prompt execution settings.</param>
    /// <returns>The invoke request body per model requirements for the InvokeAsync Bedrock runtime call.</returns>
    internal object GetInvokeModelRequestBody(string modelId, string prompt, PromptExecutionSettings? executionSettings = null);

    /// <summary>
    /// Extracts the text contents from the <see cref="InvokeModelResponse"/>.
    /// </summary>
    /// <param name="response">The <see cref="InvokeModelResponse"/> instance to be returned from the InvokeAsync Bedrock call.</param>
    /// <returns>The list of TextContent objects for the Semantic Kernel output.</returns>
    internal IReadOnlyList<TextContent> GetInvokeResponseBody(InvokeModelResponse response);

    /// <summary>
    /// Converts the streaming JSON into <see cref="IEnumerable{String}"/> for output.
    /// </summary>
    /// <param name="chunk">The payloadPart bytes provided from the streaming response.</param>
    /// <returns><see cref="IEnumerable{String}"/> output strings.</returns>
    internal IEnumerable<StreamingTextContent> GetTextStreamOutput(JsonNode chunk);
}
