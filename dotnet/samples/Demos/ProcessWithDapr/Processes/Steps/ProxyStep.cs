// Copyright (c) Microsoft. All rights reserved.

using Microsoft.AspNetCore.SignalR.Client;
using Microsoft.SemanticKernel;

namespace FormFilling;

/// <summary>
/// Step that is helps the user fill up a new account form.<br/>
/// Also provides a welcome message for the user.
/// TODO-estenori: working step
/// </summary>
public class HackyProxyStep : KernelProcessStep
{
    public static class Functions
    {
        public const string EmitWelcomeMessage = nameof(EmitWelcomeMessage);
        public const string EmitNewFormAssistantMessage = nameof(EmitNewFormAssistantMessage);
        public const string EmitNewFormAssistantMessageNoReply = nameof(EmitNewFormAssistantMessageNoReply);
        public const string EmitCompletedForm = nameof(EmitCompletedForm);
    }

    private HubConnection GetHubConnection()
    {
        var hubConnection = new HubConnectionBuilder()
            .WithUrl("https://localhost:58844/chatHub")
            .Build();

        return hubConnection;
    }

    [KernelFunction(Functions.EmitWelcomeMessage)]
    public async Task<string> EmitWelcomeMessageAsync(string assistantMessage)
    {
        var hubConnection = this.GetHubConnection();

        var tcs = new TaskCompletionSource<string>();
        hubConnection.On<string>("onUserMessage", tcs.SetResult);

        await hubConnection.StartAsync();

        await hubConnection.InvokeAsync("SendAssistantMessageAsync", assistantMessage);
        var userMessage = await tcs.Task;
        hubConnection.Remove("onUserMessage");

        await hubConnection.StopAsync();

        return userMessage;
    }

    [KernelFunction(Functions.EmitNewFormAssistantMessage)]
    public async Task<string> EmitNewFormAssistantMessageAsync(string assistantMessage)
    {
        var hubConnection = this.GetHubConnection();

        var tcs = new TaskCompletionSource<string>();
        hubConnection.On<string>("onUserMessage", tcs.SetResult);

        await hubConnection.StartAsync();

        await hubConnection.InvokeAsync("SendAssistantMessageAsync", assistantMessage);
        var userMessage = await tcs.Task;
        hubConnection.Remove("onUserMessage");
        await hubConnection.StopAsync();

        return userMessage;
    }

    [KernelFunction(Functions.EmitNewFormAssistantMessageNoReply)]
    public async Task EmitNewFormAssistantMessageNoReplyAsync(string assistantMessage)
    {
        var hubConnection = this.GetHubConnection();

        await hubConnection.StartAsync();
        await hubConnection.InvokeAsync("SendAssistantMessageAsync", assistantMessage);
        await hubConnection.StopAsync();
    }

    [KernelFunction(Functions.EmitCompletedForm)]
    public async Task EmitCompletedFormAsync(object completedForm)
    {
        var hubConnection = this.GetHubConnection();

        await hubConnection.StartAsync();
        await hubConnection.InvokeAsync("onFormCompleted", completedForm);
        await hubConnection.StopAsync();
    }
}

public enum FormCompletionEvents
{
    InitializeProxy,
    //OnWelcomeMessageReady, // May not be necessary
    OnEmitAssistantMessageWithUserReply,
    OnUserReplyFromAssistantMessageRequested,
    OnUserReplyFromAssistantMessage,
    OnEmitAssistantMessageWithoutUserReply,
    OnFormCompleted,
    OnUserResponseReceived,
}

public class AlternativeProxyStep : KernelProcessProxyStep<FormCompletionEvents>
{
    /// <summary>
    /// To be triggered on Initialization of Proxy step
    /// Similar to onMount -> to be invoked only once
    /// </summary>
    /// <returns></returns>
    /// <exception cref="NotImplementedException"></exception>
    public override Task InitializeServerConnection()
    {
        throw new NotImplementedException();
    }

    /// <summary>
    /// Works like regular step function
    /// ADAPTATION:
    /// - 
    /// </summary>
    /// <param name="externalContext">New "externalContext" to trigger external events, to be passed similarly like KernelProcessStepContext</param>
    /// <param name="internalContext">existing <see cref="KernelProcessStepContext"/> to trigger SK process events</param>
    /// <param name="assistantMessage">regular SK process input param</param>
    /// <returns></returns>
    [KernelProcessEventProxy(FormCompletionEvents.OnEmitAssistantMessageWithUserReply)]
    public async Task EmitNewFormAssistantMessageAsync(KernelProcessProxyStepExternalContext externalContext, KernelProcessStepContext internalContext, string assistantMessage)
    {
        // emitting external event with external context
        await externalContext.EmitExternalEventAsync("SendAssistantMessageAsync", assistantMessage);
        // emitting internal event meant to be intercepted by OnUserReplyFromAssistantFormReplyAsync -> responseRequested param
        await internalContext.EmitEventAsync(this.GetProcessEventName(FormCompletionEvents.OnUserReplyFromAssistantMessageRequested), true);
    }

    public async Task OnUserReplyFromAssistantFormReplyAsync(
        // input param to be received from SK process event OnUserReplyFromAssistantMessageRequested
        // should this internal event be internal to proxy step?
        [KernelProcessEventProxyParameter(FormCompletionEvents.OnUserReplyFromAssistantMessageRequested)] bool responseRequested,
        // input param to be received when external sourec receives subscribed "topic" onUserMessage
        [KernelProcessExternalEventProxyParameter("onUserMessage")] string userReply,
        KernelProcessStepContext internalContext
        )
    {
        await internalContext.EmitEventAsync(this.GetProcessEventName(FormCompletionEvents.OnUserResponseReceived), userReply);
    }

    [KernelProcessEventProxy(FormCompletionEvents.OnEmitAssistantMessageWithoutUserReply)]
    public async Task EmitNewFormAssistantMessageWithNoReplyAsync(KernelProcessProxyStepExternalContext externalContext, string assistantMessage)
    {
        // emits external event/topic SendAssistantMessageAsync on assistantMessage received
        await externalContext.EmitExternalEventAsync("SendAssistantMessageAsync", assistantMessage);
    }

    [KernelProcessEventProxy(FormCompletionEvents.OnFormCompleted)]
    public async Task EmitFormCompletedAsync(KernelProcessProxyStepExternalContext externalContext, object completedForm)
    {
        // emits external event/topic onFormCompleted on completedForm received
        await externalContext.EmitExternalEventAsync("onFormCompleted", completedForm);
    }
}
