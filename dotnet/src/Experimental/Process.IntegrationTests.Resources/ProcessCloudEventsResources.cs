// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel;

namespace SemanticKernel.Process.IntegrationTests;

#pragma warning disable CS1591 // Missing XML comment for publicly visible type or member

/// <summary>
/// A step that emits messages externally
/// </summary>
public sealed class MockProxyStep : KernelProcessStep
{
    public static class FunctionNames
    {
        public const string OnRepeatMessage = nameof(OnRepeatMessage);
        public const string OnEchoMessage = nameof(OnEchoMessage);
    }

    public static class TopicNames
    {
        public const string RepeatExternalTopic = nameof(RepeatExternalTopic);
        public const string EchoExternalTopic = nameof(EchoExternalTopic);
    }

    [KernelFunction(FunctionNames.OnRepeatMessage)]
    public async Task OnRepeatMessageAsync(KernelProcessStepContext context, string message)
    {
        await context.EmitExternalEventAsync(TopicNames.RepeatExternalTopic, message);
    }

    [KernelFunction(FunctionNames.OnEchoMessage)]
    public async Task OnEchoMessageAsync(KernelProcessStepContext context, string message)
    {
        await context.EmitExternalEventAsync(TopicNames.EchoExternalTopic, message);
    }
}

#pragma warning restore CS1591 // Missing XML comment for publicly visible type or member
