// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Dapr.Actors.Runtime;
using Microsoft.AspNetCore.SignalR.Client;
using Microsoft.SemanticKernel.Process.Interfaces;

namespace Microsoft.SemanticKernel.Process.Actors;
public class SignalRActor : Actor, ISignalRClient
{
    private HubConnection _hubConnection;
    private string _processId;

    public SignalRActor(ActorHost host, string processId) : base(host)
    {
        this._hubConnection = new HubConnectionBuilder()
            .WithUrl("")
            .Build();

        this._hubConnection.StartAsync().GetAwaiter().GetResult();
        this._processId = processId;

        // there should be a mapping of signalR event : SK process event
        this._hubConnection.On<string, object?>("someSignalRTopic", this.OnEmitProcessInputEventAsync);
    }

    private async Task OnEmitProcessInputEventAsync(string processEventId, object? data)
    {
        var daprProcess = this.ProxyFactory.CreateActorProxy<IProcess>(new Dapr.Actors.ActorId(this._processId), nameof(ProcessActor));
        // Process should already be running - why does it need DaprProcessInfo
        // how to check process is alive?
        KernelProcessEvent processEvent = new() { Id = processEventId, Data = data };
        await daprProcess.SendMessageAsync(processEvent.ToString()).ConfigureAwait(false);
    }

    public async Task PublishMessageExternallyAsync(string topic, object? data)
    {
        await this._hubConnection.InvokeAsync(topic, data).ConfigureAwait(false);
    }

    protected override Task OnDeactivateAsync()
    {
        // Cleanup SignalR connection on Actor Deactivation
        this._hubConnection.StopAsync().GetAwaiter().GetResult();
        return base.OnDeactivateAsync();
    }
}
