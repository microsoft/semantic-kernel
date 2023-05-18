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
    private readonly string _receiveMessageClientCall = "ReceiveMessage";
    private readonly string _receiveTypingStateClientCall = "ReceiveTypingState";
    private readonly string _receiveFileUploadedEventClientCall = "ReceiveFileUploadedEvent";
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
    /// <param name="chatId"></param>
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
        await this.Clients.OthersInGroup(chatId).SendAsync(this._receiveMessageClientCall, message, chatId);
    }

    /// <summary>
    /// Sends the typing state to all users except the sender.
    /// </summary>
    /// <param name="chatId">The ChatID used as group id for SignalR.</param>
    /// <param name="isTypingState">The typing state to send to other clients.</param>
    /// <returns>A task that represents the asynchronous operation.</returns>
    public async Task SendTypingStateAsync(string chatId, object isTypingState)
    {
        await this.Clients.OthersInGroup(chatId).SendAsync(this._receiveTypingStateClientCall, isTypingState, chatId);
    }

    /// <summary>
    /// Sends the information about a file that was uploade to the server. Sent to all users except the sender.
    /// </summary>
    /// <param name="chatId">The ChatID used as group id for SignalR.</param>
    /// <param name="fileUploadedAlert">Information about a file that was uploaded by another user</param>
    /// <returns>A task that represents the asynchronous operation.</returns>
    public async Task SendFileUploadedEventAsync(string chatId, object fileUploadedAlert)
    {
        await this.Clients.OthersInGroup(chatId).SendAsync(this._receiveFileUploadedEventClientCall, fileUploadedAlert, chatId);
    }
}
