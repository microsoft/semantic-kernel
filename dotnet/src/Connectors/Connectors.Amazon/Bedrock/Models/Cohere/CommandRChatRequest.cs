// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Connectors.Amazon.Core.Requests;

namespace Connectors.Amazon.Models.Cohere;

public class CohereCommandRequest : IChatCompletionRequest
{
    [JsonPropertyName("message")]
    public string Message { get; set; }

    public List<Message> Messages { get; set; }
    // List<Message> IChatCompletionRequest.Messages { get; set; }

    // List<Message> IChatCompletionRequest.Messages
    // {
    //     get => BedrockMessages;
    //     set => Messages = value;
    // }

    [JsonPropertyName("chat_history")]
    public List<CohereMessage> ChatHistory { get; set; }

    [JsonPropertyName("documents")]
    public List<CohereDocument> Documents { get; set; }

    [JsonPropertyName("search_queries_only")]
    public bool SearchQueriesOnly { get; set; } = false;

    [JsonPropertyName("preamble")]
    public string Preamble { get; set; }

    [JsonPropertyName("max_tokens")]
    public int MaxTokens { get; set; } = 512; // Default value

    [JsonPropertyName("temperature")]
    public double Temperature { get; set; } = 0.3; // Default value

    [JsonPropertyName("p")]
    public double TopP { get; set; } = 0.75; // Default value

    [JsonPropertyName("k")]
    public double TopK { get; set; } = 0.0; // Default value

    [JsonPropertyName("prompt_truncation")]
    public string PromptTruncation { get; set; } = "OFF"; // Default value

    [JsonPropertyName("frequency_penalty")]
    public double FrequencyPenalty { get; set; } = 0.0; // Default value

    [JsonPropertyName("presence_penalty")]
    public double PresencePenalty { get; set; } = 0.0; // Default value

    [JsonPropertyName("seed")]
    public int Seed { get; set; }

    [JsonPropertyName("return_prompt")]
    public bool ReturnPrompt { get; set; } = false;

    [JsonPropertyName("tools")]
    public List<CohereTool> Tools { get; set; }

    [JsonPropertyName("tool_results")]
    public List<CohereToolResult> ToolResults { get; set; }

    [JsonPropertyName("stop_sequences")]
    public List<string> StopSequences { get; set; }

    [JsonPropertyName("raw_prompting")]
    public bool RawPrompting { get; set; } = false;

    // public List<Message> BedrockMessages
    // {
    //     get
    //     {
    //         var messages = new List<Message>();
    //         if (ChatHistory != null)
    //         {
    //             messages.AddRange(ChatHistory.Select(m => new Message
    //             {
    //                 Role = MapRole(m.Role),
    //                 Content = new List<ContentBlock> { new ContentBlock { Text = m.Message } }
    //             }));
    //         }
    //         messages.Add(new Message
    //         {
    //             Role = ConversationRole.User,
    //             Content = new List<ContentBlock> { new ContentBlock { Text = Message } }
    //         });
    //         return messages;
    //     }
    // }

    public List<Message> BedrockMessages { get; set; }

    public List<SystemContentBlock> System { get; set; }
    public InferenceConfiguration InferenceConfig { get; set; }
    public Document AdditionalModelRequestFields { get; set; }
    public List<string> AdditionalModelResponseFieldPaths { get; set; }
    public GuardrailConfiguration GuardrailConfig { get; set; }
    public string ModelId { get; set; }
    public ToolConfiguration ToolConfig { get; set; }

    public class CohereMessage
    {
        [JsonPropertyName("role")]
        public string Role { get; set; }

        [JsonPropertyName("message")]
        public string Message { get; set; }
    }

    public class CohereDocument
    {
        [JsonPropertyName("title")]
        public string Title { get; set; }

        [JsonPropertyName("snippet")]
        public string Snippet { get; set; }
    }

    public class CohereTool
    {
        [JsonPropertyName("name")]
        public string Name { get; set; }

        [JsonPropertyName("description")]
        public string Description { get; set; }

        [JsonPropertyName("parameter_definitions")]
        public Dictionary<string, CohereToolParameter> ParameterDefinitions { get; set; }
    }

    public class CohereToolParameter
    {
        [JsonPropertyName("description")]
        public string Description { get; set; }

        [JsonPropertyName("type")]
        public string Type { get; set; }

        [JsonPropertyName("required")]
        public bool Required { get; set; }
    }

    public class CohereToolResult
    {
        [JsonPropertyName("call")]
        public CohereToolCall Call { get; set; }

        [JsonPropertyName("outputs")]
        public List<Document> Outputs { get; set; }
    }

    public class CohereToolCall
    {
        [JsonPropertyName("name")]
        public string Name { get; set; }

        [JsonPropertyName("parameters")]
        public Dictionary<string, string> Parameters { get; set; }
    }

    private string MapRole(string role)
    {
        return role.ToLower() switch
        {
            "user" => ConversationRole.User,
            "chatbot" => ConversationRole.Assistant,
            _ => throw new ArgumentException($"Invalid role: {role}")
        };
    }
}
