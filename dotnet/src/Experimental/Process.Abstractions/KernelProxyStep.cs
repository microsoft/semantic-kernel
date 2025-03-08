// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Process;

/// <summary>
/// Internal SK KernelProcessStep preconfigured to be used when emitting SK events outside of the SK Process Framework or inside with a different event name
/// </summary>
public sealed class KernelProxyStep : KernelProcessStep
{
    /// <summary>
    /// SK Function names in this SK Step as entry points
    /// </summary>
    public static class Functions
    {
        /// <summary>
        /// Function name used to emit events externally
        /// </summary>
        public const string EmitExternalEvent = nameof(EmitExternalEvent);
    }

    /// <summary>
    /// Step function used to emit events externally
    /// </summary>
    /// <param name="context">instance of <see cref="KernelProcessStepContext"/></param>
    /// <param name="proxyEvent">event data passed to proxy step</param>
    /// <returns></returns>
    [KernelFunction(Functions.EmitExternalEvent)]
    public Task EmitExternalEventAsync(KernelProcessStepContext context, KernelProcessProxyMessage proxyEvent)
    {
        Verify.NotNull(proxyEvent.ExternalTopicName, nameof(proxyEvent.ExternalTopicName));
        return context.EmitExternalEventAsync(proxyEvent);
    }
}
