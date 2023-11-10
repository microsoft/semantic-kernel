using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

public class ThreadRunModel
{
    [JsonPropertyName("id")]
    public string Id { get; set; }

    [JsonPropertyName("object")]
    public string Object { get; set; }

    [JsonPropertyName("created_at")]
    public long CreatedAt { get; set; }

    [JsonPropertyName("assistant_id")]
    public string AssistantId { get; set; }

    [JsonPropertyName("thread_id")]
    public string ThreadId { get; set; }

    [JsonPropertyName("status")]
    public string Status { get; set; }

    [JsonPropertyName("started_at")]
    public long? StartedAt { get; set; }

    [JsonPropertyName("expires_at")]
    public long? ExpiresAt { get; set; }

    [JsonPropertyName("cancelled_at")]
    public long? CancelledAt { get; set; }

    [JsonPropertyName("failed_at")]
    public long? FailedAt { get; set; }

    [JsonPropertyName("completed_at")]
    public long? CompletedAt { get; set; }

    [JsonPropertyName("last_error")]
    public ErrorModel LastError { get; set; }

    [JsonPropertyName("model")]
    public string Model { get; set; }

    [JsonPropertyName("instructions")]
    public string Instructions { get; set; }

    [JsonPropertyName("tools")]
    public List<ToolModel> Tools { get; set; }

    [JsonPropertyName("file_ids")]
    public List<string> FileIds { get; set; }

    [JsonPropertyName("metadata")]
    public Dictionary<string, object> Metadata { get; set; }

    public class ToolModel
    {
        [JsonPropertyName("type")]
        public string Type { get; set; }
    }
    public class ErrorModel
    {
        [JsonPropertyName("code")]
        public string Code { get; set; }

        [JsonPropertyName("message")]
        public string Message { get; set; }
    }
}
