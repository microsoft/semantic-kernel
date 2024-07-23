// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Connectors.Amazon.Models.Anthropic;

/// <summary>
/// Input-output service for Anthropic Claude model.
/// </summary>
public class AnthropicIOService : IBedrockModelIOService<IChatCompletionRequest, IChatCompletionResponse>,
    IBedrockModelIOService<ITextGenerationRequest, ITextGenerationResponse>
{
    private readonly BedrockUtilities _util = new();
    /// <summary>
    /// Builds InvokeModel request Body parameter with structure as required by Anthropic Claude.
    /// </summary>
    /// <param name="prompt">The input prompt for text generation.</param>
    /// <param name="executionSettings">Optional prompt execution settings.</param>
    /// <returns></returns>
    public object GetInvokeModelRequestBody(string prompt, PromptExecutionSettings? executionSettings = null)
    {
        double? temperature = 1.0; // Claude default
        double? topP = 1.0; // Claude default
        int? maxTokensToSample = 200; // Claude default
        List<string>? stopSequences = new() { "\n\nHuman:" }; // Claude default
        int? topK = 250; // Claude default

        if (executionSettings is { ExtensionData: not null })
        {
            executionSettings.ExtensionData.TryGetValue("temperature", out var temperatureValue);
            temperature = temperatureValue as double?;

            executionSettings.ExtensionData.TryGetValue("top_p", out var topPValue);
            topP = topPValue as double?;

            executionSettings.ExtensionData.TryGetValue("max_tokens_to_sample", out var maxTokensToSampleValue);
            maxTokensToSample = maxTokensToSampleValue as int?;

            executionSettings.ExtensionData.TryGetValue("stop_sequences", out var stopSequencesValue);
            stopSequences = stopSequencesValue as List<string>;

            executionSettings.ExtensionData.TryGetValue("top_k", out var topKValue);
            topK = topKValue as int?;
        }

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
        var claudeRequest = new ClaudeRequest.ClaudeChatCompletionRequest
        {
            Messages = chatHistory.Select(m => new Message
            {
                Role = new BedrockUtilities().MapRole(m.Role),
                Content = new List<ContentBlock> { new() { Text = m.Content } }
            }).ToList(),
            System = this._util.GetExtensionDataValue(settings?.ExtensionData, "system", new List<SystemContentBlock>()),
            InferenceConfig = new InferenceConfiguration
            {
                Temperature = this._util.GetExtensionDataValue(settings?.ExtensionData, "temperature", 1f),
                TopP = this._util.GetExtensionDataValue(settings?.ExtensionData, "top_p", 0.999f),
                MaxTokens = this._util.GetExtensionDataValue(settings?.ExtensionData, "max_tokens", 512)
            },
            // AnthropicVersion = "bedrock-2023-05-31", // NOTE: documentation states anthropic_version required and value must be 'bedrock-2023-05-31' but BedrockRuntime ValidationException with this field present.
            Tools = this._util.GetExtensionDataValue<List<ClaudeRequest.ClaudeChatCompletionRequest.ClaudeTool>>(settings?.ExtensionData, "tools", null),
            ToolChoice = this._util.GetExtensionDataValue<ClaudeRequest.ClaudeChatCompletionRequest.ClaudeToolChoice>(settings?.ExtensionData, "tool_choice", null)
        };
        var converseRequest = new ConverseRequest
        {
            ModelId = modelId,
            Messages = claudeRequest.Messages,
            System = claudeRequest.System,
            InferenceConfig = claudeRequest.InferenceConfig,
            AdditionalModelRequestFields = new Document
            {
                { "anthropic_version", claudeRequest.AnthropicVersion },
            }
        };

        // Tools are only unsupported for version 1 but work for all other anthropic models.
        if (modelId != "anthropic.claude-instant-v1")
        {
            converseRequest.AdditionalModelRequestFields.Add(
                "tools", new Document(claudeRequest.Tools?.Select(t => new Document
                {
                    { "name", t.Name },
                    { "description", t.Description },
                    { "input_schema", t.InputSchema }
                }).ToList() ?? new List<Document>())
            );

            converseRequest.AdditionalModelRequestFields.Add(
                "tool_choice", claudeRequest.ToolChoice != null
                    ? new Document
                    {
                        { "type", claudeRequest.ToolChoice.Type },
                        { "name", claudeRequest.ToolChoice.Name }
                    }
                    : new Document()
            );
        }

        converseRequest.AdditionalModelResponseFieldPaths = new List<string>();
        converseRequest.GuardrailConfig = null; // Set if needed
        converseRequest.ToolConfig = null; // Set if needed

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
        var claudeRequest = new ClaudeRequest.ClaudeChatCompletionRequest
        {
            Messages = chatHistory.Select(m => new Message
            {
                Role = new BedrockUtilities().MapRole(m.Role),
                Content = new List<ContentBlock> { new() { Text = m.Content } }
            }).ToList(),
            System = this._util.GetExtensionDataValue(settings?.ExtensionData, "system", new List<SystemContentBlock>()),
            InferenceConfig = new InferenceConfiguration
            {
                Temperature = this._util.GetExtensionDataValue(settings?.ExtensionData, "temperature", 1f),
                TopP = this._util.GetExtensionDataValue(settings?.ExtensionData, "top_p", 0.999f),
                MaxTokens = this._util.GetExtensionDataValue(settings?.ExtensionData, "max_tokens", 512)
            },
            // AnthropicVersion = "bedrock-2023-05-31", // NOTE: documentation states anthropic_version required and value must be 'bedrock-2023-05-31' but BedrockRuntime ValidationException with this field present.
            Tools = this._util.GetExtensionDataValue<List<ClaudeRequest.ClaudeChatCompletionRequest.ClaudeTool>>(settings?.ExtensionData, "tools", null),
            ToolChoice = this._util.GetExtensionDataValue<ClaudeRequest.ClaudeChatCompletionRequest.ClaudeToolChoice>(settings?.ExtensionData, "tool_choice", null)
        };
        var converseRequest = new ConverseStreamRequest()
        {
            ModelId = modelId,
            Messages = claudeRequest.Messages,
            System = claudeRequest.System,
            InferenceConfig = claudeRequest.InferenceConfig,
            AdditionalModelRequestFields = new Document
            {
                { "anthropic_version", claudeRequest.AnthropicVersion },
            }
        };

        // Tools are only unsupported for version 1 but work for all other anthropic models.
        if (modelId != "anthropic.claude-instant-v1")
        {
            converseRequest.AdditionalModelRequestFields.Add(
                "tools", new Document(claudeRequest.Tools?.Select(t => new Document
                {
                    { "name", t.Name },
                    { "description", t.Description },
                    { "input_schema", t.InputSchema }
                }).ToList() ?? new List<Document>())
            );

            converseRequest.AdditionalModelRequestFields.Add(
                "tool_choice", claudeRequest.ToolChoice != null
                    ? new Document
                    {
                        { "type", claudeRequest.ToolChoice.Type },
                        { "name", claudeRequest.ToolChoice.Name }
                    }
                    : new Document()
            );
        }

        converseRequest.AdditionalModelResponseFieldPaths = new List<string>();
        converseRequest.GuardrailConfig = null; // Set if needed
        converseRequest.ToolConfig = null; // Set if needed

        return converseRequest;
    }
}
