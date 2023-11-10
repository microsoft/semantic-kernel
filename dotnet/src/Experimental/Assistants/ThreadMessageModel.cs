using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

using System.Collections.Generic;

public class ThreadMessageModel
{
    [JsonPropertyName("id")]
    public string Id { get; set; }

    [JsonPropertyName("object")]
    public string Object { get; set; }

    [JsonPropertyName("created_at")]
    public long CreatedAt { get; set; }

    [JsonPropertyName("thread_id")]
    public string ThreadId { get; set; }

    [JsonPropertyName("role")]
    public string Role { get; set; }

    [JsonPropertyName("content")]
    public List<ContentModel> Content { get; set; }

    [JsonPropertyName("file_ids")]
    public List<string> FileIds { get; set; }

    [JsonPropertyName("assistant_id")]
    public string AssistantId { get; set; }

    [JsonPropertyName("run_id")]
    public string RunId { get; set; }

    [JsonPropertyName("metadata")]
    public Dictionary<string, object> Metadata { get; set; }

    public class ContentModel
    {
        [JsonPropertyName("type")]
        public string Type { get; set; }

        [JsonPropertyName("text")]
        public TextContentModel Text { get; set; }
    }

    public class TextContentModel
    {
        [JsonPropertyName("value")]
        public string Value { get; set; }

        [JsonPropertyName("annotations")]
        public List<object> Annotations { get; set; }
    }
}
