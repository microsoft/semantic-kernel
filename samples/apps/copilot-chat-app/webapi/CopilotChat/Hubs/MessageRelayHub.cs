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
    private readonly string _userConnectedClientCall = "UserConnected";
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
        await this.Clients.All.SendAsync(this._userConnectedClientCall, this.Context.ConnectionId);
        this._logger.LogInformation("User connected with connection id: {0}", this.Context.ConnectionId);
    }

    /// <summary>
    /// Sends a message to all users except the sender.
    /// </summary>
    /// <param name="clientSideCallBackName">The name of the client-side callback function.</param>
    /// <param name="message">The message to send.</param>
    /// <returns>A task that represents the asynchronous operation.</returns>
    public async Task SendMessageToAllUsersExceptSelfAsync(string clientSideCallBackName, object message)
    {
        this._logger.LogInformation("Receive message: {0}", message);
        await this.Clients.AllExcept(this.Context.ConnectionId).SendAsync(clientSideCallBackName, message);
        this._logger.LogDebug("Called SendMessageToAllUsersExceptSelfAsync on server");
        this._logger.LogDebug("Called {0} on clients", clientSideCallBackName);
    }
}
