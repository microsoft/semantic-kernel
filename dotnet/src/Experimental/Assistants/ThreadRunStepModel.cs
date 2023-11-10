using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

public class ThreadRunStepModel
{
    [JsonPropertyName("id")]
    public string Id { get; set; }

    [JsonPropertyName("object")]
    public string Object { get; set; }

    [JsonPropertyName("created_at")]
    public long CreatedAt { get; set; }

    [JsonPropertyName("run_id")]
    public string RunId { get; set; }

    [JsonPropertyName("assistant_id")]
    public string AssistantId { get; set; }

    [JsonPropertyName("thread_id")]
    public string ThreadId { get; set; }

    [JsonPropertyName("type")]
    public string Type { get; set; }

    [JsonPropertyName("status")]
    public string Status { get; set; }

    [JsonPropertyName("cancelled_at")]
    public long? CancelledAt { get; set; }

    [JsonPropertyName("completed_at")]
    public long? CompletedAt { get; set; }

    [JsonPropertyName("expired_at")]
    public long? ExpiredAt { get; set; }

    [JsonPropertyName("failed_at")]
    public long? FailedAt { get; set; }

    [JsonPropertyName("last_error")]
    public string LastError { get; set; }

    [JsonPropertyName("step_details")]
    public StepDetailsModel StepDetails { get; set; }

    public class StepDetailsModel
    {
        [JsonPropertyName("type")]
        public string Type { get; set; }

        [JsonPropertyName("message_creation")]
        public MessageCreationDetailsModel MessageCreation { get; set; }

        [JsonPropertyName("tool_calls")]
        public List<ToolCallsDetailsModel> ToolCalls { get; set; }
    }

    public class MessageCreationDetailsModel
    {
        [JsonPropertyName("message_id")]
        public string MessageId { get; set; }
    }

    public class ToolCallsDetailsModel
    {
        [JsonPropertyName("id")]
        public string Id { get; set; }

        [JsonPropertyName("type")]
        public string Type { get; set; }

        [JsonPropertyName("function")]
        public FunctionDetailsModel Function { get; set; }
    }

    public class FunctionDetailsModel
    {
        [JsonPropertyName("name")]
        public string Name { get; set; }

        [JsonPropertyName("arguments")]
        public string Arguments { get; set; }
    }
}
