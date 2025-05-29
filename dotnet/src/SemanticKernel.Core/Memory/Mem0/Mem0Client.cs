// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// Client for the Mem0 memory service.
/// </summary>
internal sealed class Mem0Client
{
    private static readonly Uri s_searchUri = new("/v1/memories/search/", UriKind.Relative);
    private static readonly Uri s_createMemoryUri = new("/v1/memories/", UriKind.Relative);

    private readonly HttpClient _httpClient;

    public Mem0Client(HttpClient httpClient)
    {
        Verify.NotNull(httpClient);

        this._httpClient = httpClient;
    }

    public async Task<IEnumerable<string>> SearchAsync(string? applicationId, string? agentId, string? threadId, string? userId, string? inputText)
    {
        if (string.IsNullOrWhiteSpace(applicationId)
            && string.IsNullOrWhiteSpace(agentId)
            && string.IsNullOrWhiteSpace(threadId)
            && string.IsNullOrWhiteSpace(userId))
        {
            throw new ArgumentException("At least one of applicationId, agentId, threadId, or userId must be provided.");
        }

        var searchRequest = new SearchRequest
        {
            AppId = applicationId,
            AgentId = agentId,
            RunId = threadId,
            UserId = userId,
            Query = inputText ?? string.Empty
        };

        // Search.
        using var content = new StringContent(JsonSerializer.Serialize(searchRequest, Mem0SourceGenerationContext.Default.SearchRequest), Encoding.UTF8, "application/json");
        var responseMessage = await this._httpClient.PostAsync(s_searchUri, content).ConfigureAwait(false);
        responseMessage.EnsureSuccessStatusCode();

        // Process response.
        var response = await responseMessage.Content.ReadAsStringAsync().ConfigureAwait(false);
        var searchResponseItems = JsonSerializer.Deserialize<SearchResponseItem[]>(response, Mem0SourceGenerationContext.Default.SearchResponseItemArray);
        return searchResponseItems?.Select(item => item.Memory) ?? [];
    }

    public async Task CreateMemoryAsync(string? applicationId, string? agentId, string? threadId, string? userId, string messageContent, string messageRole)
    {
        if (string.IsNullOrWhiteSpace(applicationId)
            && string.IsNullOrWhiteSpace(agentId)
            && string.IsNullOrWhiteSpace(threadId)
            && string.IsNullOrWhiteSpace(userId))
        {
            throw new ArgumentException("At least one of applicationId, agentId, threadId, or userId must be provided.");
        }

#pragma warning disable CA1308 // Normalize strings to uppercase: mem0 requires lowercase values
        var createMemoryRequest = new CreateMemoryRequest()
        {
            AppId = applicationId,
            AgentId = agentId,
            RunId = threadId,
            UserId = userId,
            Messages = new[]
            {
                new CreateMemoryMessage
                {
                    Content = messageContent,
                    Role = messageRole.ToLowerInvariant()
                }
            }
        };
#pragma warning restore CA1308 // Normalize strings to uppercase

        using var content = new StringContent(JsonSerializer.Serialize(createMemoryRequest, Mem0SourceGenerationContext.Default.CreateMemoryRequest), Encoding.UTF8, "application/json");
        var responseMessage = await this._httpClient.PostAsync(s_createMemoryUri, content).ConfigureAwait(false);
        responseMessage.EnsureSuccessStatusCode();
    }

    public async Task ClearMemoryAsync(string? applicationId, string? agentId, string? threadId, string? userId)
    {
        string[] paramNames = ["app_id", "agent_id", "run_id", "user_id"];

        // Build query string.
        var querystringParams = new string?[4] { applicationId, agentId, threadId, userId }
            .Select((param, index) => string.IsNullOrWhiteSpace(param) ? null : $"{paramNames[index]}={param}")
            .Where(x => x != null);
        var queryString = string.Join("&", querystringParams);
        var clearMemoryUrl = new Uri($"/v1/memories/?{queryString}", UriKind.Relative);

        // Delete.
        var responseMessage = await this._httpClient.DeleteAsync(clearMemoryUrl).ConfigureAwait(false);
        responseMessage.EnsureSuccessStatusCode();
    }

    internal sealed class CreateMemoryRequest
    {
        [JsonPropertyName("app_id")]
        public string? AppId { get; set; }
        [JsonPropertyName("agent_id")]
        public string? AgentId { get; set; }
        [JsonPropertyName("run_id")]
        public string? RunId { get; set; }
        [JsonPropertyName("user_id")]
        public string? UserId { get; set; }
        [JsonPropertyName("messages")]
        public CreateMemoryMessage[] Messages { get; set; } = [];
    }

    internal sealed class CreateMemoryMessage
    {
        [JsonPropertyName("content")]
        public string Content { get; set; } = string.Empty;
        [JsonPropertyName("role")]
        public string Role { get; set; } = string.Empty;
    }

    internal sealed class SearchRequest
    {
        [JsonPropertyName("app_id")]
        public string? AppId { get; set; }
        [JsonPropertyName("agent_id")]
        public string? AgentId { get; set; } = null;
        [JsonPropertyName("run_id")]
        public string? RunId { get; set; } = null;
        [JsonPropertyName("user_id")]
        public string? UserId { get; set; } = null;
        [JsonPropertyName("query")]
        public string Query { get; set; } = string.Empty;
    }

    internal sealed class SearchResponseItem
    {
        [JsonPropertyName("id")]
        public string Id { get; set; } = string.Empty;
        [JsonPropertyName("memory")]
        public string Memory { get; set; } = string.Empty;
        [JsonPropertyName("hash")]
        public string Hash { get; set; } = string.Empty;
        [JsonPropertyName("metadata")]
        public object? Metadata { get; set; }
        [JsonPropertyName("score")]
        public double Score { get; set; }
        [JsonPropertyName("created_at")]
        public DateTime CreatedAt { get; set; }
        [JsonPropertyName("updated_at")]
        public DateTime? UpdatedAt { get; set; }
        [JsonPropertyName("user_id")]
        public string UserId { get; set; } = string.Empty;
        [JsonPropertyName("app_id")]
        public string? AppId { get; set; }
        [JsonPropertyName("agent_id")]
        public string AgentId { get; set; } = string.Empty;
        [JsonPropertyName("session_id")]
        public string RunId { get; set; } = string.Empty;
    }
}

[JsonSourceGenerationOptions(JsonSerializerDefaults.General,
    UseStringEnumConverter = false,
    DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    WriteIndented = false)]
[JsonSerializable(typeof(Mem0Client.CreateMemoryRequest))]
[JsonSerializable(typeof(Mem0Client.SearchRequest))]
[JsonSerializable(typeof(Mem0Client.SearchResponseItem[]))]
internal partial class Mem0SourceGenerationContext : JsonSerializerContext
{
}
