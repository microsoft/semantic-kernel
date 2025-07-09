// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Dapr.Actors;
using Dapr.Actors.Runtime;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Process;
using Microsoft.SemanticKernel.Process.Internal;
using Microsoft.SemanticKernel.Process.Runtime;

namespace Microsoft.SemanticKernel;

internal sealed class ProxyActor : StepActor, IProxy
{
    private readonly ILogger? _logger;

    internal KernelProcessProxy? _proxyInfo;

    /// <summary>
    /// Initializes a new instance of the <see cref="ProxyActor"/> class.
    /// </summary>
    /// <param name="host">The Dapr host actor</param>
    /// <param name="kernel">An instance of <see cref="Kernel"/></param>
    /// <param name="registeredProcesses">The registered processes</param>
    public ProxyActor(ActorHost host, Kernel kernel, IReadOnlyDictionary<string, KernelProcess> registeredProcesses)
        : base(host, kernel, registeredProcesses)
    {
        this._logger = this._kernel.LoggerFactory?.CreateLogger(typeof(KernelProxyStep)) ?? new NullLogger<ProxyActor>();
    }

    internal override void AssignStepFunctionParameterValues(ProcessMessage message)
    {
        if (this._functions is null || this._inputs is null || this._initialInputs is null)
        {
            throw new KernelException("The step has not been initialized.").Log(this._logger);
        }

        if (message.Values.Count != 1)
        {
            throw new KernelException("The proxy step can only handle 1 parameter object").Log(this._logger);
        }

        // Add the message values to the inputs for the function
        var kvp = message.Values.Single();
        if (this._inputs.TryGetValue(message.FunctionName, out Dictionary<string, object?>? functionName) && functionName != null && functionName.TryGetValue(kvp.Key, out object? parameterName) && parameterName != null)
        {
            this._logger?.LogWarning("Step {StepName} already has input for {FunctionName}.{Key}, it is being overwritten with a message from Step named '{SourceId}'.", this.Name, message.FunctionName, kvp.Key, message.SourceId);
        }

        if (!this._inputs.TryGetValue(message.FunctionName, out Dictionary<string, object?>? functionParameters))
        {
            this._inputs[message.FunctionName] = [];
            functionParameters = this._inputs[message.FunctionName];
        }

        if (this._proxyInfo?.ProxyMetadata != null && message.SourceEventId != null && this._proxyInfo.ProxyMetadata.EventMetadata.TryGetValue(message.SourceEventId, out var metadata) && metadata != null)
        {
            functionParameters![kvp.Key] = KernelProcessProxyMessageFactory.CreateProxyMessage(this.ParentProcessId!, message.SourceEventId, metadata.TopicName, kvp.Value);
        }
    }

    internal override Dictionary<string, Dictionary<string, object?>?> GenerateInitialInputs()
    {
        // Creating external process channel actor to be used for only by proxy step actor
        IExternalKernelProcessMessageChannel? externalMessageChannelActor = null;
        var scopedExternalMessageBufferId = this.ScopedActorId(new ActorId(this.Id.GetId()));
        IExternalMessageBuffer actor = this.ProxyFactory.CreateActorProxy<IExternalMessageBuffer>(scopedExternalMessageBufferId, nameof(ExternalMessageBufferActor));
        externalMessageChannelActor = new ExternalMessageBufferActorWrapper(actor);

        // Proxy step does not emit output events, no output event data is needed
        return this.FindInputChannels(this._functions, null, this._logger, externalMessageChannelActor);
    }

    public async Task InitializeProxyAsync(string processId, string stepId, string? parentProcessId)
    {
        Verify.NotNullOrWhiteSpace(processId, nameof(processId));
        Verify.NotNullOrWhiteSpace(stepId, nameof(stepId));

        this._proxyInfo = this._registeredProcesses.GetStepInfo<KernelProcessProxy>(processId, stepId);
        await base.InitializeStepAsync(processId, stepId, parentProcessId).ConfigureAwait(false);
    }
}
