// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.AspNetCore.Cors;
using Microsoft.AspNetCore.SignalR;
using Microsoft.SemanticKernel;

namespace ProcessWithDapr.Hubs;

record ChatMessage
{
    [JsonPropertyName("senderId")]
    public string SenderId { get; set; }

    [JsonPropertyName("content")]
    public string Content { get; set; }
}


[EnableCors("CorsPolicy")]
public class ChatHub : Hub
{
    private int _counter = 0;
    private List<ChatMessage> _messages = [];

    public async Task SendUserMessageAsync(string user, string message)
    {
        this._counter++;
        // emiting user message
        ChatMessage userMessage = new() { SenderId = user, Content = message };
        this._messages.Add(userMessage);
        await this.Clients.All.SendAsync("ReceiveMessage", userMessage.SenderId, userMessage.Content);
        await this.Clients.All.SendAsync("onUserMessage", userMessage.Content);
    }

    public async Task SendAssistantMessageAsync(string message)
    {
        this._counter++;
        // emiting assistant message
        ChatMessage userMessage = new() { SenderId = "Assistant", Content = message };
        this._messages.Add(userMessage);
        await this.Clients.All.SendAsync("ReceiveMessage", userMessage.SenderId, userMessage.Content);
    }

    public async Task JoinConversationAsync(string conversationId)
    {
        await this.Clients.All.SendAsync("ConversationHistory", this._messages);
    }

    public async Task ResetConversationAsync(string conversationId)
    {
        this._messages.Clear();
        await this.Clients.All.SendAsync("ConversationReset");
    }
}
