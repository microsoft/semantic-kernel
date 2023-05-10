// Copyright (c) Microsoft. All rights reserved.

using Microsoft.AspNetCore.SignalR;
using Microsoft.Extensions.Options;
using SemanticKernel.Service.Config;
using SemanticKernel.Service.Controllers;

namespace SemanticKernel.Service.SignalR.Hubs;

public class ChatHub : Hub
{
    private readonly ILogger<ChatHub> _logger;

    public ChatHub(ILogger<ChatHub> logger)
    {
        this._logger = logger;
    }

    public async Task SendConversationToOtherUsersAsync(object message)
    {
        await this.Clients.AllExcept(this.Context.ConnectionId).SendAsync("SendMessage", message);
        this._logger.LogInformation("Called SendConversationToOtherUsersAsync");
    }

    public async Task SendMessageToAllUsersExceptSelfAsync(string ClientSideCallBackName, string message)
    {
        await this.Clients.AllExcept(this.Context.ConnectionId).SendAsync(ClientSideCallBackName, message);
        this._logger.LogInformation("Called SendMessageToAllUsersExceptSelfAsync");
    }

    public async Task SendMessageToAllUsersAsync(string message)
    {
        await this.Clients.AllExcept(this.Context.ConnectionId).SendAsync("ReceiveMessage", message);
        this._logger.LogInformation("Called SendMessageToAllUsersAsync");
    }

    public async Task ReceiveMessageAsync(string user, string message)
    {
        await this.Clients.All.SendAsync("ReceiveMessage", user, message);
        this._logger.LogInformation("Called ReceiveMessage");
    }

    public override async Task OnConnectedAsync()
    {
        await this.Clients.All.SendAsync("UserConnected", this.Context.ConnectionId);
        this._logger.LogInformation("Log UserConnected");
    }
}
