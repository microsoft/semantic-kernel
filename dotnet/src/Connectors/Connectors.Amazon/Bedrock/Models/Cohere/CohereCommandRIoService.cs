// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Connectors.Amazon.Models.Cohere;

public class CohereCommandRIoService : IBedrockModelIoService<IChatCompletionRequest, IChatCompletionResponse>,
    IBedrockModelIoService<ITextGenerationRequest, ITextGenerationResponse>
{
    public object GetInvokeModelRequestBody(string text, PromptExecutionSettings executionSettings)
    {
        double? temperature = 0.3; // Cohere default
        double? topP = 0.75; // Cohere default
        int? maxTokens = null; // Cohere default
        List<string>? stopSequences = null;
        double? topK = 0; // Cohere default
        string promptTruncation = "OFF"; // Cohere default
        double? frequencyPenalty = 0; // Cohere default
        double? presencePenalty = 0; // Cohere default
        int? seed = null;
        bool? returnPrompt = false; // Cohere default
        List<CommandRTextRequest.Tool>? tools = null;
        List<CommandRTextRequest.ToolResult>? toolResults = null;
        bool? rawPrompting = false; // Cohere default

        if (executionSettings != null && executionSettings.ExtensionData != null)
        {
            executionSettings.ExtensionData.TryGetValue("temperature", out var temperatureValue);
            temperature = temperatureValue as double?;

            executionSettings.ExtensionData.TryGetValue("p", out var topPValue);
            topP = topPValue as double?;

            executionSettings.ExtensionData.TryGetValue("k", out var topKValue);
            topK = topKValue as double?;

            executionSettings.ExtensionData.TryGetValue("max_tokens", out var maxTokensValue);
            maxTokens = maxTokensValue as int?;

            executionSettings.ExtensionData.TryGetValue("stop_sequences", out var stopSequencesValue);
            stopSequences = stopSequencesValue as List<string>;

            executionSettings.ExtensionData.TryGetValue("prompt_truncation", out var promptTruncationValue);
            promptTruncation = promptTruncationValue as string;

            executionSettings.ExtensionData.TryGetValue("frequency_penalty", out var frequencyPenaltyValue);
            frequencyPenalty = frequencyPenaltyValue as double?;

            executionSettings.ExtensionData.TryGetValue("presence_penalty", out var presencePenaltyValue);
            presencePenalty = presencePenaltyValue as double?;

            executionSettings.ExtensionData.TryGetValue("seed", out var seedValue);
            seed = seedValue as int?;

            executionSettings.ExtensionData.TryGetValue("return_prompt", out var returnPromptValue);
            returnPrompt = returnPromptValue as bool?;

            executionSettings.ExtensionData.TryGetValue("tools", out var toolsValue);
            tools = toolsValue as List<CommandRTextRequest.Tool>;

            executionSettings.ExtensionData.TryGetValue("tool_results", out var toolResultsValue);
            toolResults = toolResultsValue as List<CommandRTextRequest.ToolResult>;

            executionSettings.ExtensionData.TryGetValue("raw_prompting", out var rawPromptingValue);
            rawPrompting = rawPromptingValue as bool?;
        }

        var requestBody = new CommandRTextRequest.CommandRTextGenerationRequest
        {
            Message = text,
            Temperature = temperature,
            TopP = topP,
            TopK = topK,
            MaxTokens = maxTokens,
            StopSequences = stopSequences,
            PromptTruncation = promptTruncation,
            FrequencyPenalty = frequencyPenalty,
            PresencePenalty = presencePenalty,
            Seed = seed,
            ReturnPrompt = returnPrompt,
            Tools = tools,
            ToolResults = toolResults,
            RawPrompting = rawPrompting
        };

        return requestBody;
    }

    public IReadOnlyList<TextContent> GetInvokeResponseBody(InvokeModelResponse response)
    {
        using (var memoryStream = new MemoryStream())
        {
            response.Body.CopyToAsync(memoryStream).ConfigureAwait(false).GetAwaiter().GetResult();
            memoryStream.Position = 0;
            using (var reader = new StreamReader(memoryStream))
            {
                var responseBody = JsonSerializer.Deserialize<CommandRTextResponse>(reader.ReadToEnd());
                var textContents = new List<TextContent>();

                if (!string.IsNullOrEmpty(responseBody?.Text))
                {
                    textContents.Add(new TextContent(responseBody.Text));
                }

                return textContents;
            }
        }
    }
    public ConverseRequest GetConverseRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings = null)
    {
        var cohereRequest = new CohereCommandRequest
    {
        // Message = chatHistory.Any() ? chatHistory[^1].Content : string.Empty,
        ChatHistory = chatHistory.Select(m => new CohereCommandRequest.CohereMessage
        {
            Role = MapRole(m.Role),
            Message = m.Content
        }).ToList(),
        Messages = chatHistory.Select(m => new Message
        {
            Role = MapRole(m.Role),
            Content = new List<ContentBlock> { new ContentBlock { Text = m.Content } }
        }).ToList(),
        Temperature = this.GetExtensionDataValue<double>(settings?.ExtensionData, "temperature", 0.3),
        TopP = this.GetExtensionDataValue<double>(settings?.ExtensionData, "p", 0.75),
        TopK = this.GetExtensionDataValue<double>(settings?.ExtensionData, "k", 0.0),
        MaxTokens = this.GetExtensionDataValue<int>(settings?.ExtensionData, "max_tokens", 512),
        PromptTruncation = this.GetExtensionDataValue<string>(settings?.ExtensionData, "prompt_truncation", "OFF"),
        FrequencyPenalty = this.GetExtensionDataValue<double>(settings?.ExtensionData, "frequency_penalty", 0.0),
        PresencePenalty = this.GetExtensionDataValue<double>(settings?.ExtensionData, "presence_penalty", 0.0),
        Seed = this.GetExtensionDataValue<int>(settings?.ExtensionData, "seed", 0),
        ReturnPrompt = this.GetExtensionDataValue<bool>(settings?.ExtensionData, "return_prompt", false),
        Tools = this.GetExtensionDataValue<List<CohereCommandRequest.CohereTool>>(settings?.ExtensionData, "tools", null),
        ToolResults = this.GetExtensionDataValue<List<CohereCommandRequest.CohereToolResult>>(settings?.ExtensionData, "tool_results", null),
        StopSequences = this.GetExtensionDataValue<List<string>>(settings?.ExtensionData, "stop_sequences", null),
        RawPrompting = this.GetExtensionDataValue<bool>(settings?.ExtensionData, "raw_prompting", false)
    };
    var converseRequest = new ConverseRequest
    {
        ModelId = modelId,
        Messages = cohereRequest.Messages,
        System = cohereRequest.System,
        InferenceConfig = new InferenceConfiguration
        {
            Temperature = (float)cohereRequest.Temperature,
            TopP = (float)cohereRequest.TopP,
            MaxTokens = cohereRequest.MaxTokens
        },
        AdditionalModelRequestFields = new Document
        {
            { "message", cohereRequest.Message },
            { "chat_history", new Document(cohereRequest.ChatHistory.Select(m => new Document
            {
                { "role", m.Role.ToUpper() },
                { "message", m.Message }
            }).ToList()) },
            { "documents", new Document(cohereRequest.Documents?.Select(d => new Document
            {
                { "title", d.Title },
                { "snippet", d.Snippet }
            }).ToList() ?? new List<Document>()) },
            { "search_queries_only", cohereRequest.SearchQueriesOnly },
            { "preamble", cohereRequest.Preamble },
            { "k", cohereRequest.TopK },
            { "prompt_truncation", cohereRequest.PromptTruncation },
            { "frequency_penalty", cohereRequest.FrequencyPenalty },
            { "presence_penalty", cohereRequest.PresencePenalty },
            { "seed", cohereRequest.Seed },
            { "return_prompt", cohereRequest.ReturnPrompt },
            { "stop_sequences", new Document(cohereRequest.StopSequences?.Select(s => new Document(s)).ToList() ?? new List<Document>()) },
            { "raw_prompting", cohereRequest.RawPrompting }
        },
        AdditionalModelResponseFieldPaths = new List<string>(),
        GuardrailConfig = null,
        ToolConfig = null
        // ToolConfig = new ToolConfiguration
        // {
        //     Tools = new List<Tool>(cohereRequest.Tools.Select(t => new Tool
        //     {
        //         ToolSpec = new ToolSpecification
        //         {
        //             Name = t.Name,
        //             Description = t.Description,
        //             InputSchema = new ToolInputSchema
        //             {
        //                 Json = new Document(t.ParameterDefinitions.ToDictionary(kvp => kvp.Key, kvp => new Document
        //                 {
        //                     { "description", kvp.Value.Description },
        //                     { "type", kvp.Value.Type },
        //                     { "required", kvp.Value.Required }
        //                 }))
        //             }
        //         }
        //     })),
        //     ToolChoice = cohereRequest.Tools?.Any() == true
        //         ? new ToolChoice { Any = new AnyToolChoice() }
        //         : new ToolChoice { Auto = new AutoToolChoice() }
        // }

        // ToolConfig = new Document
        // {
        //     { "tools", new Document(cohereRequest.Tools?.Select(t => new Document
        //         {
        //             { "name", t.Name },
        //             { "description", t.Description },
        //             { "parameter_definitions", new Document(t.ParameterDefinitions.Select(p => new KeyValuePair<string, Document>(p.Key, new Document
        //                 {
        //                     { "description", p.Value.Description },
        //                     { "type", p.Value.Type },
        //                     { "required", p.Value.Required }
        //                 })).ToDictionary<KeyValuePair<string, Document>, string, Document>(kvp => kvp.Key, kvp => kvp.Value))
        //             }
        //         }).ToList() ?? new List<Document>())
        //     },
        //     { "tool_results", new Document(cohereRequest.ToolResults?.Select(tr => new Document
        //         {
        //             { "call", new Document
        //                 {
        //                     { "name", tr.Call.Name },
        //                     { "parameters", new Document(tr.Call.Parameters.Select(p => new KeyValuePair<string, Document>(p.Key, new Document(p.Value))).ToDictionary<KeyValuePair<string, Document>, string, Document>(kvp => kvp.Key, kvp => kvp.Value)) }
        //                 }
        //             },
        //             { "outputs", new Document(tr.Outputs) }
        //         }).ToList() ?? new List<Document>())
        //     }
        // }
    };

    return converseRequest;
    }

    private static ConversationRole MapRole(AuthorRole role)
    {
        if (role == AuthorRole.User)
        {
            return ConversationRole.User;
        }
        if (role == AuthorRole.Assistant)
        {
            return ConversationRole.Assistant;
        }
        throw new ArgumentOutOfRangeException(nameof(role), $"Invalid role: {role}");
    }

    private TValue GetExtensionDataValue<TValue>(IDictionary<string, object>? extensionData, string key, TValue defaultValue)
    {
        if (extensionData == null || !extensionData.TryGetValue(key, out object? value))
        {
            return defaultValue;
        }

        if (value is TValue typedValue)
        {
            return typedValue;
        }

        return defaultValue;
    }

    public IEnumerable<string> GetTextStreamOutput(JsonNode chunk)
    {
        var text = chunk?["text"]?.ToString();
        if (!string.IsNullOrEmpty(text))
        {
            yield return text;
        }
    }

    //FOR COMMAND R ONLY (command does not support chat streaming)
    public ConverseStreamRequest GetConverseStreamRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings settings)
    {
        var cohereRequest = new CohereCommandRequest
    {
        // Message = chatHistory.Any() ? chatHistory[^1].Content : string.Empty,
        ChatHistory = chatHistory.Select(m => new CohereCommandRequest.CohereMessage
        {
            Role = MapRole(m.Role),
            Message = m.Content
        }).ToList(),
        Messages = chatHistory.Select(m => new Message
        {
            Role = MapRole(m.Role),
            Content = new List<ContentBlock> { new ContentBlock { Text = m.Content } }
        }).ToList(),
        Temperature = this.GetExtensionDataValue<double>(settings?.ExtensionData, "temperature", 0.3),
        TopP = this.GetExtensionDataValue<double>(settings?.ExtensionData, "p", 0.75),
        TopK = this.GetExtensionDataValue<double>(settings?.ExtensionData, "k", 0.0),
        MaxTokens = this.GetExtensionDataValue<int>(settings?.ExtensionData, "max_tokens", 512),
        PromptTruncation = this.GetExtensionDataValue<string>(settings?.ExtensionData, "prompt_truncation", "OFF"),
        FrequencyPenalty = this.GetExtensionDataValue<double>(settings?.ExtensionData, "frequency_penalty", 0.0),
        PresencePenalty = this.GetExtensionDataValue<double>(settings?.ExtensionData, "presence_penalty", 0.0),
        Seed = this.GetExtensionDataValue<int>(settings?.ExtensionData, "seed", 0),
        ReturnPrompt = this.GetExtensionDataValue<bool>(settings?.ExtensionData, "return_prompt", false),
        Tools = this.GetExtensionDataValue<List<CohereCommandRequest.CohereTool>>(settings?.ExtensionData, "tools", null),
        ToolResults = this.GetExtensionDataValue<List<CohereCommandRequest.CohereToolResult>>(settings?.ExtensionData, "tool_results", null),
        StopSequences = this.GetExtensionDataValue<List<string>>(settings?.ExtensionData, "stop_sequences", null),
        RawPrompting = this.GetExtensionDataValue<bool>(settings?.ExtensionData, "raw_prompting", false)
    };
    var converseStreamRequest = new ConverseStreamRequest
    {
        ModelId = modelId,
        Messages = cohereRequest.Messages,
        System = cohereRequest.System,
        InferenceConfig = new InferenceConfiguration
        {
            Temperature = (float)cohereRequest.Temperature,
            TopP = (float)cohereRequest.TopP,
            MaxTokens = cohereRequest.MaxTokens
        },
        AdditionalModelRequestFields = new Document
        {
            { "message", cohereRequest.Message },
            { "documents", new Document(cohereRequest.Documents?.Select(d => new Document
            {
                { "title", d.Title },
                { "snippet", d.Snippet }
            }).ToList() ?? new List<Document>()) },
            { "search_queries_only", cohereRequest.SearchQueriesOnly },
            { "preamble", cohereRequest.Preamble },
            { "k", cohereRequest.TopK },
            { "prompt_truncation", cohereRequest.PromptTruncation },
            { "frequency_penalty", cohereRequest.FrequencyPenalty },
            { "presence_penalty", cohereRequest.PresencePenalty },
            { "seed", cohereRequest.Seed },
            { "return_prompt", cohereRequest.ReturnPrompt },
            { "stop_sequences", new Document(cohereRequest.StopSequences?.Select(s => new Document(s)).ToList() ?? new List<Document>()) },
            { "raw_prompting", cohereRequest.RawPrompting }
        },
        AdditionalModelResponseFieldPaths = new List<string>(),
        GuardrailConfig = null,
        ToolConfig = null
    };

    return converseStreamRequest;
    }
}
