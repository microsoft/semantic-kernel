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
    private const string ReceiveMessageClientCall = "ReceiveMessage";
    private const string ReceiveUserTypingStateClientCall = "ReceiveUserTypingState";
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
    /// Adds the user to the groups that they are a member of.
    /// Groups are identified by the chat ID.
    /// TODO: Retrieve the user ID from the claims and call this method
    /// from the OnConnectedAsync method instead of the frontend.
    /// </summary>
    /// <param name="chatId">The ChatID used as group id for SignalR.</param>
    public async Task AddClientToGroupAsync(string chatId)
    {
        await this.Groups.AddToGroupAsync(this.Context.ConnectionId, chatId);
    }

    /// <summary>
    /// Sends a message to all users except the sender.
    /// </summary>
    /// <param name="chatId">The ChatID used as group id for SignalR.</param>
    /// <param name="message">The message to send.</param>
    public async Task SendMessageAsync(string chatId, object message)
    {
        await this.Clients.OthersInGroup(chatId).SendAsync(ReceiveMessageClientCall, message, chatId);
    }

    /// <summary>
    /// Sends the typing state to all users except the sender.
    /// </summary>
    /// <param name="chatId">The ChatID used as group id for SignalR.</param>
    /// <param name="userId">The user ID of the user who is typing.</param>
    /// <param name="isTyping">Whether the user is typing.</param>
    /// <returns>A task that represents the asynchronous operation.</returns>
    public async Task SendUserTypingStateAsync(string chatId, string userId, bool isTyping)
    {
        await this.Clients.OthersInGroup(chatId).SendAsync(ReceiveUserTypingStateClientCall, chatId, userId, isTyping);
    }
}
