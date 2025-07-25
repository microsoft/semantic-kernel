// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides step related functionality for Kernel Functions running in a step.
/// </summary>
public sealed class KernelProcessStepContext
{
    private readonly IKernelProcessMessageChannel _stepMessageChannel;
    private readonly IKernelProcessUserStateStore? _userStateStore;

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessStepContext"/> class.
    /// </summary>
    /// <param name="channel">An instance of <see cref="IKernelProcessMessageChannel"/>.</param>
    public KernelProcessStepContext(IKernelProcessMessageChannel channel, IKernelProcessUserStateStore? userStateStore = null)
    {
        this._stepMessageChannel = channel;
        this._userStateStore = userStateStore;
    }

    /// <summary>
    /// Emit an SK process event from the current step.
    /// </summary>
    /// <param name="processEvent">An instance of <see cref="KernelProcessEvent"/> to be emitted from the <see cref="KernelProcessStep"/></param>
    /// <returns>A <see cref="ValueTask"/></returns>
    public ValueTask EmitEventAsync(KernelProcessEvent processEvent)
    {
        return this._stepMessageChannel.EmitEventAsync(processEvent);
    }

    /// <summary>
    /// Emit an SK process event from the current step with a simplified method signature.
    /// </summary>
    /// <param name="eventId"></param>
    /// <param name="data"></param>
    /// <param name="visibility"></param>
    /// <returns></returns>
    public ValueTask EmitEventAsync(
        string eventId,
        object? data = null,
        KernelProcessEventVisibility visibility = KernelProcessEventVisibility.Internal)
    {
        Verify.NotNullOrWhiteSpace(eventId, nameof(eventId));

        return this._stepMessageChannel.EmitEventAsync(
            new KernelProcessEvent
            {
                Id = eventId,
                Data = data,
                Visibility = visibility
            });
    }

    /// <summary>
    /// Gets the user state of the process.
    /// </summary>
    /// <param name="key">The key to identify the user state.</param>
    /// <typeparam name="T"></typeparam>
    /// <returns></returns>
    public Task<T> GetUserStateAsync<T>(string key) where T : class
    {
        return this._userStateStore?.GetUserStateAsync<T>(key) ?? Task.FromResult<T>(null!);
    }

    /// <summary>
    /// Sets the user state of the process.
    /// </summary>
    /// <typeparam name="T"></typeparam>
    /// <param name="key"></param>
    /// <param name="state"></param>
    /// <returns></returns>
    public Task SetUserStateAsync<T>(string key, T state) where T : class
    {
        return this._userStateStore?.SetUserStateAsync(key, state) ?? Task.CompletedTask;
    }
}
