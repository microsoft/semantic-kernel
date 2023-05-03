// Copyright (c) Microsoft. All rights reserved.

using Microsoft.AspNetCore.SignalR;

namespace SemanticKernel.Service.SignalR.Hubs;

public class ChatHub : Hub
{
#pragma warning disable IDE1006 // Naming Styles
    public async Task SendMessage(string user, string message)
    {
        await this.Clients.All.SendAsync("SendMessage", user, message);
        Console.WriteLine("Log SendMessage: {0}", message);
    }

    public async Task ReceiveMessage(string user, string message)
    {
        await this.Clients.All.SendAsync("ReceiveMessage", user, message);
        Console.WriteLine("Log ReceiveMessage: {0}", message);
    }

    public override async Task OnConnectedAsync()
    {
        await this.Clients.All.SendAsync("UserConnected", this.Context.ConnectionId);
        Console.WriteLine("Log UserConnected");
    }

    public async Task NewMessage(long username, string message)
#pragma warning restore IDE1006 // Naming Styles
    {
        await this.Clients.All.SendAsync("messageReceived", username, message);
        Console.WriteLine("Log messageReceived: {0}", message);
    }
        
}
