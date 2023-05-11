// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.AspNetCore.SignalR;
using Microsoft.Extensions.Logging;

namespace SemanticKernel.Service.CopilotChat.Hubs;

/// <summary>
/// Represents a chat hub for real-time communication.
/// </summary>
public class MessageRelayHub : Hub
{
    private readonly string UserConnectedClientCall = "UserConnected";
    private readonly string ReceiveMessageClientCall = "ReceiveMessage";
    private readonly ILogger<MessageRelayHub> _logger;

    /// <summary>
    /// Initializes a new instance of the <see cref="MessageRelayHub"/> class.
    /// </summary>
    /// <param name="logger">The logger.</param>
    public MessageRelayHub(ILogger<MessageRelayHub> logger)
    {
        this._logger = logger;
    }

    /// <summary>
    /// Called when a client connects to the hub.
    /// </summary>
    public override async Task OnConnectedAsync()
    {
        await this.Clients.All.SendAsync(UserConnectedClientCall, this.Context.ConnectionId);
        this._logger.LogInformation("User connected with connection id: {0}", this.Context.ConnectionId);
    }

    /// <summary>
    /// Sends a conversation message to all other users except the sender.
    /// </summary>
    /// <param name="message">The message to send.</param>
    public async Task SendMessage(object message)
    {
        this._logger.LogInformation("Receive message: {0}", message);
        await this.Clients.AllExcept(this.Context.ConnectionId).SendAsync(ReceiveMessageClientCall, message);
        this._logger.LogDebug("Called {0}", ReceiveMessageClientCall);
    }
}