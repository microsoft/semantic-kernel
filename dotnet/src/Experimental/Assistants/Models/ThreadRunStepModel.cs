// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Experimental.Assistants.Models;

public class ThreadRunStepModel
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("object")]
    public string Object { get; set; } = string.Empty;

    [JsonPropertyName("created_at")]
    public long CreatedAt { get; set; }

    [JsonPropertyName("run_id")]
    public string RunId { get; set; } = string.Empty;

    [JsonPropertyName("assistant_id")]
    public string AssistantId { get; set; } = string.Empty;

    [JsonPropertyName("thread_id")]
    public string ThreadId { get; set; } = string.Empty;

    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    [JsonPropertyName("status")]
    public string Status { get; set; } = string.Empty;

    [JsonPropertyName("cancelled_at")]
    public long? CancelledAt { get; set; }

    [JsonPropertyName("completed_at")]
    public long? CompletedAt { get; set; }

    [JsonPropertyName("expired_at")]
    public long? ExpiredAt { get; set; }

    [JsonPropertyName("failed_at")]
    public long? FailedAt { get; set; }

    [JsonPropertyName("last_error")]
    public string LastError { get; set; } = string.Empty;

    [JsonPropertyName("step_details")]
    public StepDetailsModel StepDetails { get; set; }

    public class StepDetailsModel
    {
        [JsonPropertyName("type")]
        public string Type { get; set; } = string.Empty;

        [JsonPropertyName("message_creation")]
        public MessageCreationDetailsModel MessageCreation { get; set; }

        [JsonPropertyName("tool_calls")]
        public List<ToolCallsDetailsModel> ToolCalls { get; set; }
    }

    public class MessageCreationDetailsModel
    {
        [JsonPropertyName("message_id")]
        public string MessageId { get; set; } = string.Empty;
    }

    public class ToolCallsDetailsModel
    {
        [JsonPropertyName("id")]
        public string Id { get; set; } = string.Empty;

        [JsonPropertyName("type")]
        public string Type { get; set; } = string.Empty;

        [JsonPropertyName("function")]
        public FunctionDetailsModel Function { get; set; }
    }

    public class FunctionDetailsModel
    {
        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyName("arguments")]
        public string Arguments { get; set; } = string.Empty;
    }
}
