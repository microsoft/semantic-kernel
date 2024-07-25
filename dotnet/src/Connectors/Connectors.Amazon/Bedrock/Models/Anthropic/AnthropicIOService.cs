// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Connectors.Amazon.Models.Anthropic;

/// <summary>
/// Input-output service for Anthropic Claude model.
/// </summary>
public class AnthropicIOService : IBedrockModelIOService
{
    private readonly BedrockModelUtilities _util = new();

    // Define constants for default values
    private const double DefaultTemperature = 1.0;
    private const double DefaultTopP = 1.0;
    private const int DefaultMaxTokensToSample = 4096;
    private static readonly List<string> DefaultStopSequences = new() { "\n\nHuman:" };
    private const int DefaultTopK = 250;
    /// <summary>
    /// Builds InvokeModel request Body parameter with structure as required by Anthropic Claude.
    /// </summary>
    /// <param name="modelId">The model ID to be used as a request parameter.</param>
    /// <param name="prompt">The input prompt for text generation.</param>
    /// <param name="executionSettings">Optional prompt execution settings.</param>
    /// <returns></returns>
    public object GetInvokeModelRequestBody(string modelId, string prompt, PromptExecutionSettings? executionSettings = null)
    {
        var temperature = this._util.GetExtensionDataValue(executionSettings?.ExtensionData, "temperature", (double?)DefaultTemperature);
        var topP = this._util.GetExtensionDataValue(executionSettings?.ExtensionData, "top_p", (double?)DefaultTopP);
        var maxTokensToSample = this._util.GetExtensionDataValue(executionSettings?.ExtensionData, "max_tokens_to_sample", (int?)DefaultMaxTokensToSample);
        var stopSequences = this._util.GetExtensionDataValue(executionSettings?.ExtensionData, "stop_sequences", DefaultStopSequences);
        var topK = this._util.GetExtensionDataValue(executionSettings?.ExtensionData, "top_k", (int?)DefaultTopK);

        var requestBody = new ClaudeRequest.ClaudeTextGenerationRequest()
        {
            Prompt = $"\n\nHuman: {prompt}\n\nAssistant:",
            MaxTokensToSample = maxTokensToSample,
            StopSequences = stopSequences,
            Temperature = temperature,
            TopP = topP,
            TopK = topK
        };

        return requestBody;
    }
    /// <summary>
    /// Extracts the test contents from the InvokeModelResponse as returned by the Bedrock API.
    /// </summary>
    /// <param name="response">The InvokeModelResponse object provided by the Bedrock InvokeModelAsync output.</param>
    /// <returns></returns>
    public IReadOnlyList<TextContent> GetInvokeResponseBody(InvokeModelResponse response)
    {
        using (var memoryStream = new MemoryStream())
        {
            response.Body.CopyToAsync(memoryStream).ConfigureAwait(false).GetAwaiter().GetResult();
            memoryStream.Position = 0;
            using (var reader = new StreamReader(memoryStream))
            {
                var responseBody = JsonSerializer.Deserialize<ClaudeResponse>(reader.ReadToEnd());
                var textContents = new List<TextContent>();

                if (!string.IsNullOrEmpty(responseBody?.Completion))
                {
                    textContents.Add(new TextContent(responseBody.Completion));
                }

                return textContents;
            }
        }
    }

    /// <summary>
    /// Builds the ConverseRequest object for the Bedrock ConverseAsync call with request parameters required by Anthropic Claude.
    /// </summary>
    /// <param name="modelId">The model ID.</param>
    /// <param name="chatHistory">The messages between assistant and user.</param>
    /// <param name="settings">Optional prompt execution settings.</param>
    /// <returns></returns>
    public ConverseRequest GetConverseRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings = null)
    {
        var messages = chatHistory.Select(m => new Message
        {
            Role = new BedrockModelUtilities().MapRole(m.Role),
            Content = new List<ContentBlock> { new() { Text = m.Content } }
        }).ToList();

        var system = this._util.GetExtensionDataValue(settings?.ExtensionData, "system", new List<SystemContentBlock>());

        var inferenceConfig = new InferenceConfiguration
        {
            Temperature = this._util.GetExtensionDataValue(settings?.ExtensionData, "temperature", (float)DefaultTemperature),
            TopP = this._util.GetExtensionDataValue(settings?.ExtensionData, "top_p", (float)DefaultTopP),
            MaxTokens = this._util.GetExtensionDataValue(settings?.ExtensionData, "max_tokens_to_sample", DefaultMaxTokensToSample)
        };

        var additionalModelRequestFields = new Document { };

        var tools = this._util.GetExtensionDataValue<List<ClaudeRequest.ClaudeChatCompletionRequest.ClaudeTool>>(settings?.ExtensionData, "tools", null);
        var toolChoice = this._util.GetExtensionDataValue<ClaudeRequest.ClaudeChatCompletionRequest.ClaudeToolChoice>(settings?.ExtensionData, "tool_choice", null);

        if (modelId != "anthropic.claude-instant-v1")
        {
            additionalModelRequestFields.Add(
                "tools", new Document(tools?.Select(t => new Document
                {
                    { "name", t.Name },
                    { "description", t.Description },
                    { "input_schema", t.InputSchema }
                }).ToList() ?? new List<Document>())
            );

            additionalModelRequestFields.Add(
                "tool_choice", toolChoice != null
                    ? new Document
                    {
                        { "type", toolChoice.Type },
                        { "name", toolChoice.Name }
                    }
                    : new Document()
            );
        }

        var converseRequest = new ConverseRequest
        {
            ModelId = modelId,
            Messages = messages,
            System = system,
            InferenceConfig = inferenceConfig,
            AdditionalModelRequestFields = additionalModelRequestFields,
            AdditionalModelResponseFieldPaths = new List<string>(),
            GuardrailConfig = null, // Set if needed
            ToolConfig = null // Set if needed
        };

        return converseRequest;
    }
    /// <summary>
    /// Extracts the text generation streaming output from the Anthropic Claude response object structure.
    /// </summary>
    /// <param name="chunk"></param>
    /// <returns></returns>
    public IEnumerable<string> GetTextStreamOutput(JsonNode chunk)
    {
        var text = chunk["completion"]?.ToString();
        if (!string.IsNullOrEmpty(text))
        {
            yield return text;
        }
    }

    /// <summary>
    /// Builds the ConverseStreamRequest object for the Converse Bedrock API call, including building the Anthropic Claude Request object and mapping parameters to the ConverseStreamRequest object.
    /// </summary>
    /// <param name="modelId">The model ID.</param>
    /// <param name="chatHistory">The messages between assistant and user.</param>
    /// <param name="settings">Optional prompt execution settings.</param>
    /// <returns></returns>
    public ConverseStreamRequest GetConverseStreamRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings = null)
    {
        var messages = chatHistory.Select(m => new Message
        {
            Role = new BedrockModelUtilities().MapRole(m.Role),
            Content = new List<ContentBlock> { new() { Text = m.Content } }
        }).ToList();

        var system = this._util.GetExtensionDataValue(settings?.ExtensionData, "system", new List<SystemContentBlock>());

        var inferenceConfig = new InferenceConfiguration
        {
            Temperature = this._util.GetExtensionDataValue(settings?.ExtensionData, "temperature", (float)DefaultTemperature),
            TopP = this._util.GetExtensionDataValue(settings?.ExtensionData, "top_p", (float)DefaultTopP),
            MaxTokens = this._util.GetExtensionDataValue(settings?.ExtensionData, "max_tokens_to_sample", DefaultMaxTokensToSample)
        };

        var additionalModelRequestFields = new Document { };

        var tools = this._util.GetExtensionDataValue<List<ClaudeRequest.ClaudeChatCompletionRequest.ClaudeTool>>(settings?.ExtensionData, "tools", null);
        var toolChoice = this._util.GetExtensionDataValue<ClaudeRequest.ClaudeChatCompletionRequest.ClaudeToolChoice>(settings?.ExtensionData, "tool_choice", null);

        if (modelId != "anthropic.claude-instant-v1")
        {
            additionalModelRequestFields.Add(
                "tools", new Document(tools?.Select(t => new Document
                {
                    { "name", t.Name },
                    { "description", t.Description },
                    { "input_schema", t.InputSchema }
                }).ToList() ?? new List<Document>())
            );

            additionalModelRequestFields.Add(
                "tool_choice", toolChoice != null
                    ? new Document
                    {
                        { "type", toolChoice.Type },
                        { "name", toolChoice.Name }
                    }
                    : new Document()
            );
        }

        var converseRequest = new ConverseStreamRequest
        {
            ModelId = modelId,
            Messages = messages,
            System = system,
            InferenceConfig = inferenceConfig,
            AdditionalModelRequestFields = additionalModelRequestFields,
            AdditionalModelResponseFieldPaths = new List<string>(),
            GuardrailConfig = null, // Set if needed
            ToolConfig = null // Set if needed
        };

        return converseRequest;
    }
}
