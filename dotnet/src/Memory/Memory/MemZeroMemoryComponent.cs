// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// A component that listenes to messages added to the conversation thread, and automatically captures
/// information about the user. It is also able to retrieve this information and add it to the AI invocation context.
/// </summary>
public class MemZeroMemoryComponent : ThreadExtension
{
    private static readonly Uri s_searchUri = new("/search", UriKind.Relative);
    private static readonly Uri s_createMemoryUri = new("/memories", UriKind.Relative);

    private readonly string? _agentId;
    private string? _threadId;
    private readonly string? _userId;
    private readonly bool _scopeToThread;
    private readonly HttpClient _httpClient;

    private bool _contextLoaded = false;
    private string _userInformation = string.Empty;

    /// <summary>
    /// Initializes a new instance of the <see cref="MemZeroMemoryComponent"/> class.
    /// </summary>
    /// <param name="httpClient">The HTTP client used for making requests.</param>
    /// <param name="agentId">The ID of the agent.</param>
    /// <param name="threadId">The ID of the thread.</param>
    /// <param name="userId">The ID of the user.</param>
    /// <param name="scopeToThread">Indicates whether the scope is limited to the thread.</param>
    public MemZeroMemoryComponent(HttpClient httpClient, string? agentId = default, string? threadId = default, string? userId = default, bool scopeToThread = false)
    {
        Verify.NotNull(httpClient);

        this._agentId = agentId;
        this._threadId = threadId;
        this._userId = userId;
        this._scopeToThread = scopeToThread;
        this._httpClient = httpClient;
    }

    /// <inheritdoc/>
    public override Task OnThreadCreatedAsync(string? threadId, CancellationToken cancellationToken = default)
    {
        this._threadId ??= threadId;
        return Task.CompletedTask;
    }

    /// <inheritdoc/>
    public override async Task OnNewMessageAsync(ChatMessageContent newMessage, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(newMessage);

        if (newMessage.Role == AuthorRole.User)
        {
            await this.CreateMemoryAsync(
                new CreateMemoryRequest()
                {
                    AgentId = this._agentId,
                    RunId = this._scopeToThread ? this._threadId : null,
                    UserId = this._userId,
                    Messages = new[]
                    {
                        new CreateMemoryMemory
                        {
                            Content = newMessage.Content ?? string.Empty,
                            Role = newMessage.Role.Label
                        }
                    }
                }).ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    public override async Task<string> OnAIInvocationAsync(ICollection<ChatMessageContent> newMessages, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(newMessages);

        string input = string.Join("\n", newMessages.Where(m => m is not null).Select(m => m.Content));

        await this.LoadContextAsync(this._threadId, input).ConfigureAwait(false);

        return "The following list contains facts about the user:\n" + this._userInformation;
    }

    /// <inheritdoc/>
    public override void RegisterPlugins(Kernel kernel)
    {
        Verify.NotNull(kernel);

        base.RegisterPlugins(kernel);
        kernel.Plugins.AddFromObject(this, "MemZeroMemory");
    }

    /// <summary>
    /// Plugin method to clear user preferences stored in memory for the current agent/thread/user.
    /// </summary>
    /// <returns>A task that completes when the memory is cleared.</returns>
    [KernelFunction]
    [Description("Deletes any user preferences stored about the user.")]
    public async Task ClearUserPreferencesAsync()
    {
        await this.ClearMemoryAsync().ConfigureAwait(false);
    }

    private async Task LoadContextAsync(string? threadId, string? inputText)
    {
        if (!this._contextLoaded)
        {
            this._threadId ??= threadId;

            var searchRequest = new SearchRequest
            {
                AgentId = this._agentId,
                RunId = this._scopeToThread ? this._threadId : null,
                UserId = this._userId,
                Query = inputText ?? string.Empty
            };
            var responseItems = await this.SearchAsync(searchRequest).ConfigureAwait(false);
            this._userInformation = string.Join("\n", responseItems);
            this._contextLoaded = true;
        }
    }

    private async Task CreateMemoryAsync(CreateMemoryRequest createMemoryRequest)
    {
        using var content = new StringContent(JsonSerializer.Serialize(createMemoryRequest), Encoding.UTF8, "application/json");
        var responseMessage = await this._httpClient.PostAsync(s_createMemoryUri, content).ConfigureAwait(false);
        responseMessage.EnsureSuccessStatusCode();
    }

    private async Task<string[]> SearchAsync(SearchRequest searchRequest)
    {
        using var content = new StringContent(JsonSerializer.Serialize(searchRequest), Encoding.UTF8, "application/json");
        var responseMessage = await this._httpClient.PostAsync(s_searchUri, content).ConfigureAwait(false);
        responseMessage.EnsureSuccessStatusCode();
        var response = await responseMessage.Content.ReadAsStringAsync().ConfigureAwait(false);
        var searchResponseItems = JsonSerializer.Deserialize<SearchResponseItem[]>(response);
        return searchResponseItems?.Select(item => item.Memory).ToArray() ?? Array.Empty<string>();
    }

    private async Task ClearMemoryAsync()
    {
        try
        {
            var querystringParams = new string?[3] { this._userId, this._agentId, this._scopeToThread ? this._threadId : null }
                .Where(x => !string.IsNullOrWhiteSpace(x))
                .Select((param, index) => $"param{index}={param}");
            var queryString = string.Join("&", querystringParams);
            var clearMemoryUrl = new Uri($"/memories?{queryString}", UriKind.Relative);

            var responseMessage = await this._httpClient.DeleteAsync(clearMemoryUrl).ConfigureAwait(false);
            responseMessage.EnsureSuccessStatusCode();
        }
        catch (Exception ex)
        {
            Console.WriteLine($"- MemZeroMemory - Error clearing memory: {ex.Message}");
            throw;
        }
    }

    private sealed class CreateMemoryRequest
    {
        [JsonPropertyName("agent_id")]
        public string? AgentId { get; set; }
        [JsonPropertyName("run_id")]
        public string? RunId { get; set; }
        [JsonPropertyName("user_id")]
        public string? UserId { get; set; }
        [JsonPropertyName("messages")]
        public CreateMemoryMemory[] Messages { get; set; } = [];
    }

    private sealed class CreateMemoryMemory
    {
        [JsonPropertyName("content")]
        public string Content { get; set; } = string.Empty;
        [JsonPropertyName("role")]
        public string Role { get; set; } = string.Empty;
    }

    private sealed class SearchRequest
    {
        [JsonPropertyName("agent_id")]
        public string? AgentId { get; set; } = null;
        [JsonPropertyName("run_id")]
        public string? RunId { get; set; } = null;
        [JsonPropertyName("user_id")]
        public string? UserId { get; set; } = null;
        [JsonPropertyName("query")]
        public string Query { get; set; } = string.Empty;
    }

#pragma warning disable CA1812 // Avoid uninstantiated internal classes
    private sealed class SearchResponseItem
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
        [JsonPropertyName("agent_id")]
        public string AgentId { get; set; } = string.Empty;
        [JsonPropertyName("run_id")]
        public string RunId { get; set; } = string.Empty;
    }
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
}
