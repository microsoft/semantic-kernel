// Copyright (c) Microsoft. All rights reserved.

using Microsoft.AspNetCore.SignalR;

namespace SemanticKernel.Service.SignalR.Hubs;

public class ChatHub : Hub
{
    public async Task SendMessageAsync(string user, string message)
    {
        await this.Clients.All.SendAsync("SendMessage", user, message);
        Console.WriteLine("Log SendMessage: {0}", message);
    }

    public async Task SendMessageToAllUsersExceptSelfAsync(string ClientSideCallBackName, string message)
    {
        await this.Clients.AllExcept(this.Context.ConnectionId).SendAsync(ClientSideCallBackName, message);
        Console.WriteLine("Log SendMessageToAllUsersExceptSelfAsync: {0}", message);
    }

    public async Task SendMessageToAllUsersAsync(string message)
    {
        await this.Clients.AllExcept(this.Context.ConnectionId).SendAsync("ReceiveMessage", message);
        Console.WriteLine("Log SendMessageToAllUsersAsync: {0}", message);
    }

    public async Task Func2Async(string user, string message)
    {
        await this.Clients.AllExcept(this.Context.ConnectionId).SendAsync("ReceiveMessage", user, message);
        Console.WriteLine("Log ReceiveMessage: {0}", message);
    }

    public async Task ReceiveMessageAsync(string user, string message)
    {
        await this.Clients.All.SendAsync("ReceiveMessage", user, message);
        Console.WriteLine("Log ReceiveMessage: {0}", message);
    }

    public override async Task OnConnectedAsync()
    {
        await this.Clients.All.SendAsync("UserConnected", this.Context.ConnectionId);
        Console.WriteLine("Log UserConnected");
    }

    public async Task NewMessageAsync(long username, string message)
    {
        await this.Clients.All.SendAsync("messageReceived", username, message);
        Console.WriteLine("Log messageReceived: {0}", message);
    }

}
