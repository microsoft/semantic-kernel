// Copyright (c) Microsoft. All rights reserved.

using Microsoft.AspNetCore.SignalR;

namespace SemanticKernel.Service.SignalR.Hubs;

/// <summary>
/// Represents a chat hub for real-time communication.
/// </summary>
public class ChatHub : Hub
{
    private readonly ILogger<ChatHub> _logger;

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatHub"/> class.
    /// </summary>
    /// <param name="logger">The logger.</param>
    public ChatHub(ILogger<ChatHub> logger)
    {
        this._logger = logger;
    }

    /// <summary>
    /// Called when a client connects to the hub.
    /// </summary>
    public override async Task OnConnectedAsync()
    {
        await this.Clients.All.SendAsync("UserConnected", this.Context.ConnectionId);
        this._logger.LogInformation("Log UserConnected with connection id: {0}", this.Context.ConnectionId);
    }

    /// <summary>
    /// Sends a conversation message to all other users except the sender.
    /// </summary>
    /// <param name="message">The message to send.</param>
    public async Task SendConversationToOtherUsersAsync(object message)
    {
        await this.Clients.AllExcept(this.Context.ConnectionId).SendAsync("SendMessage", message);
        this._logger.LogDebug("Called SendConversationToOtherUsersAsync");
    }

    /// <summary>
    /// Sends a message to all users except the sender.
    /// </summary>
    /// <param name="ClientSideCallBackName">The name of the client-side callback function.</param>
    /// <param name="message">The message to send.</param>
    /// <returns>A task that represents the asynchronous operation.</returns>
    public async Task SendMessageToAllUsersExceptSelfAsync(string ClientSideCallBackName, string message)
    {
        await this.Clients.AllExcept(this.Context.ConnectionId).SendAsync(ClientSideCallBackName, message);
        this._logger.LogDebug("Called SendMessageToAllUsersExceptSelfAsync");
    }
}
