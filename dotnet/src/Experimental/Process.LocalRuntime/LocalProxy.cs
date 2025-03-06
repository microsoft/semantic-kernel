// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Process.Internal;
using Microsoft.SemanticKernel.Process.Runtime;

namespace Microsoft.SemanticKernel;

internal sealed class LocalProxy : LocalStep
{
    private readonly KernelProcessProxy _proxy;
    private readonly ILogger _logger;

    private bool _isInitialized = false;

    /// <summary>
    /// Initializes a new instance of the <see cref="LocalMap"/> class.
    /// </summary>
    /// <param name="proxy">an instance of <see cref="KernelProcessProxy"/></param>
    /// <param name="kernel">An instance of <see cref="Kernel"/></param>
    internal LocalProxy(KernelProcessProxy proxy, Kernel kernel)
        : base(proxy, kernel)
    {
        this._proxy = proxy;
        this._logger = this._kernel.LoggerFactory?.CreateLogger(this._proxy.State.Name) ?? new NullLogger<LocalStep>();
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

        var kvp = message.Values.Single();

        if (this._inputs.TryGetValue(message.FunctionName, out Dictionary<string, object?>? functionName) && functionName != null && functionName.TryGetValue(kvp.Key, out object? parameterName) && parameterName != null)
        {
            this._logger.LogWarning("Step {StepName} already has input for {FunctionName}.{Key}, it is being overwritten with a message from Step named '{SourceId}'.", this.Name, message.FunctionName, kvp.Key, message.SourceId);
        }

        if (!this._inputs.TryGetValue(message.FunctionName, out Dictionary<string, object?>? functionParameters))
        {
            this._inputs[message.FunctionName] = [];
            functionParameters = this._inputs[message.FunctionName];
        }

        if (this._proxy.ProxyMetadata != null && message.SourceEventId != null && this._proxy.ProxyMetadata.EventMetadata.TryGetValue(message.SourceEventId, out var metadata) && metadata != null)
        {
            functionParameters![kvp.Key] = KernelProcessProxyMessageFactory.CreateProxyMessage(this.ParentProcessId!, message.SourceEventId, metadata.TopicName, kvp.Value);
        }
    }

    /// <inheritdoc/>
    protected override async ValueTask InitializeStepAsync()
    {
        if (this._isInitialized)
        {
            return;
        }

        // Ensure initialization happens only once if first time or again if "deinitialization" was called
        if (this.ExternalMessageChannel == null)
        {
            throw new KernelException("No IExternalKernelProcessMessageChannel found, need at least 1 to emit external messages");
        }

        await this.ExternalMessageChannel.Initialize().ConfigureAwait(false);
        await base.InitializeStepAsync().ConfigureAwait(false);
        this._isInitialized = true;
    }
}
