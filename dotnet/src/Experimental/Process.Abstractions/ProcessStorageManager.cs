// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Process.Models.Storage;

namespace Microsoft.SemanticKernel.Process;

/// <summary>
/// Storage manager for storing step and process related data using the implementation of <see cref="IProcessStorageConnector"/>.
/// </summary>
public class ProcessStorageManager : IProcessStepStorageOperations, IProcessStorageOperations
{
    internal static class StorageKeywords
    {
        // Types
        /// <summary>
        /// To be used for storing process children data, parent info and external events
        /// </summary>
        public const string ProcessDetails = nameof(ProcessDetails);

        public const string StepDetails = nameof(StepDetails);
    }

    private readonly IProcessStorageConnector _storageConnector;

    private bool _isInitialized = false;

    private readonly ConcurrentDictionary<string, object> _softSaveStorage = [];

    /// <summary>
    /// Constructor for the <see cref="ProcessStorageManager"/> class.
    /// </summary>
    /// <param name="storageConnector"></param>
    public ProcessStorageManager(IProcessStorageConnector storageConnector)
    {
        this._storageConnector = storageConnector;
    }

    /// <summary>
    /// Initialize the storage connection.
    /// </summary>
    /// <returns></returns>
    public async Task<bool> InitializeAsync()
    {
        if (this._isInitialized)
        {
            return true;
        }
        await this._storageConnector.OpenConnectionAsync().ConfigureAwait(false);
        this._isInitialized = true;

        return this._isInitialized;
    }

    /// <summary>
    /// Close the storage connection.
    /// </summary>
    /// <returns></returns>
    public async Task<bool> CloseAsync()
    {
        if (!this._isInitialized)
        {
            return true;
        }
        await this._storageConnector.CloseConnectionAsync().ConfigureAwait(false);
        this._isInitialized = false;

        return true;
    }

    private string GetEntryId(string componentName, string componentId)
    {
        return $"{componentId}.{componentName}";
    }

    private string GetProcessEntryId(KernelProcess process)
    {
        Verify.NotNullOrWhiteSpace(process.StepId);
        Verify.NotNullOrWhiteSpace(process.RunId);

        return $"{this.GetEntryId(process.StepId, process.RunId)}.{StorageKeywords.ProcessDetails}";
        //return process.RunId;
    }

    private string GetStepEntryId(KernelProcessStepInfo stepInfo)
    {
        Verify.NotNullOrWhiteSpace(stepInfo.StepId);
        Verify.NotNullOrWhiteSpace(stepInfo.RunId);

        return $"{this.GetEntryId(stepInfo.StepId, stepInfo.RunId)}.{StorageKeywords.StepDetails}";
        //return step.RunId;
    }

    /// <inheritdoc/>
    public async Task FetchProcessDataAsync(KernelProcess process)
    {
        var entryId = this.GetProcessEntryId(process);

        var storageState = await this._storageConnector.GetEntryAsync<StorageProcessData>(entryId).ConfigureAwait(false);
        if (storageState != null)
        {
            this._softSaveStorage[entryId] = storageState;
        }
    }

    /// <inheritdoc/>
    public async Task<StorageProcessInfo?> GetProcessInfoAsync(KernelProcess process)
    {
        var entryId = this.GetProcessEntryId(process);
        if (this._softSaveStorage.TryGetValue(entryId, out var softSaveProcessData) && softSaveProcessData is StorageProcessData processData)
        {
            return processData.ProcessInfo;
        }
        return null;
    }

    /// <inheritdoc/>
    public async Task<bool> SaveProcessInfoAsync(KernelProcess process)
    {
        Verify.NotNullOrWhiteSpace(process.RunId);

        var entryId = this.GetProcessEntryId(process);
        if (!this._softSaveStorage.TryGetValue(entryId, out var processSavedData))
        {
            processSavedData = new StorageProcessData() { InstanceId = process.RunId };
            this._softSaveStorage.TryAdd(entryId, processSavedData);
        }

        if (processSavedData is StorageProcessData processData)
        {
            processData.ProcessInfo = process.ToKernelStorageProcessInfo();
        }

        return true;
    }

    /// <inheritdoc/>
    public async Task<bool> SaveProcessEventsAsync(KernelProcess process, List<KernelProcessEvent>? pendingExternalEvents = null)
    {
        Verify.NotNullOrWhiteSpace(process.RunId);

        var entryId = this.GetProcessEntryId(process);
        if (!this._softSaveStorage.TryGetValue(entryId, out var processSavedData))
        {
            processSavedData = new StorageProcessData() { InstanceId = process.RunId };
            this._softSaveStorage.TryAdd(entryId, processSavedData);
        }

        if (processSavedData is StorageProcessData processData)
        {
            processData.ProcessEvents = process.ToKernelStorageProcessEvents(pendingExternalEvents);
        }

        return true;
    }

    /// <inheritdoc/>
    public async Task<bool> SaveProcessDataToStorageAsync(KernelProcess process)
    {
        var entryId = this.GetProcessEntryId(process);
        if (this._softSaveStorage.TryGetValue(entryId, out var softSaveProcessData) && softSaveProcessData is StorageProcessData processData)
        {
            // for now process only has one entry - in the future the process state may be saved in a separate entity -> 2 storage calls
            return await this._storageConnector.SaveEntryAsync(entryId, StorageKeywords.ProcessDetails, processData).ConfigureAwait(false);
        }

        return false;
    }

    /// <inheritdoc/>
    public async Task FetchStepDataAsync(KernelProcessStepInfo stepInfo)
    {
        var entryId = this.GetStepEntryId(stepInfo);
        var storageState = await this._storageConnector.GetEntryAsync<StorageStepData>(entryId).ConfigureAwait(false);

        if (storageState != null)
        {
            this._softSaveStorage[entryId] = storageState;
        }
    }

    /// <inheritdoc/>
    public async Task<StorageStepInfo?> GetStepInfoAsync(KernelProcessStepInfo stepInfo)
    {
        var entryId = this.GetStepEntryId(stepInfo);
        if (this._softSaveStorage.TryGetValue(entryId, out var softSaveStepData) && softSaveStepData is StorageStepData stepData)
        {
            return stepData.StepInfo;
        }
        return null;
    }

    /// <inheritdoc/>
    public async Task<bool> SaveStepInfoAsync(KernelProcessStepInfo stepInfo)
    {
        Verify.NotNullOrWhiteSpace(stepInfo.RunId);

        var entryId = this.GetStepEntryId(stepInfo);
        if (!this._softSaveStorage.TryGetValue(entryId, out var stepSavedData))
        {
            stepSavedData = new StorageStepData() { InstanceId = stepInfo.RunId };
            this._softSaveStorage.TryAdd(entryId, stepSavedData);
        }

        if (stepSavedData is StorageStepData stepData)
        {
            stepData.StepInfo = stepInfo.ToStorageStepInfo();
        }

        return true;
    }

    /// <inheritdoc/>
    public async Task<KernelProcessStepState?> GetStepStateAsync(KernelProcessStepInfo stepInfo)
    {
        var entryId = this.GetStepEntryId(stepInfo);
        if (this._softSaveStorage.TryGetValue(entryId, out var softSaveStepData) && softSaveStepData is StorageStepData stepData)
        {
            return stepData.ToKernelProcessStepState();
        }

        return null;
    }

    public async Task<bool> SaveStepStateAsync(KernelProcessStepInfo stepInfo)
    {
        Verify.NotNullOrWhiteSpace(stepInfo.RunId);

        var entryId = this.GetStepEntryId(stepInfo);

        if (!this._softSaveStorage.TryGetValue(entryId, out var stepSavedData))
        {
            stepSavedData = new StorageStepData() { InstanceId = stepInfo.RunId };
            this._softSaveStorage.TryAdd(entryId, stepSavedData);
        }

        if (stepSavedData is StorageStepData stepData)
        {
            stepData.StepState = stepInfo.ToStorageStepState();
        }

        return true;
    }

    /// <inheritdoc/>
    public async Task<StorageStepEvents?> GetStepEventsAsync(KernelProcessStepInfo stepInfo)
    {
        var entryId = this.GetStepEntryId(stepInfo);
        if (this._softSaveStorage.TryGetValue(entryId, out var softSaveStepData) && softSaveStepData is StorageStepData stepData)
        {
            return stepData.StepEvents;
        }

        return null;
    }

    /// <inheritdoc/>
    public async Task<bool> SaveStepEventsAsync(KernelProcessStepInfo stepInfo, Dictionary<string, Dictionary<string, object?>>? edgeGroups = null)
    {
        Verify.NotNullOrWhiteSpace(stepInfo.RunId);
        var entryId = this.GetStepEntryId(stepInfo);

        if (!this._softSaveStorage.TryGetValue(entryId, out var stepSavedData))
        {
            stepSavedData = new StorageStepData() { InstanceId = stepInfo.RunId };
            this._softSaveStorage.TryAdd(entryId, stepSavedData);
        }
        if (stepSavedData is StorageStepData stepData && edgeGroups != null)
        {
            stepData.StepEvents = stepInfo.ToStorageStepEvents(edgeGroups);
        }
        return true;
    }

    /// <inheritdoc/>
    public async Task<bool> SaveStepDataToStorageAsync(KernelProcessStepInfo stepInfo)
    {
        var entryId = this.GetStepEntryId(stepInfo);
        if (this._softSaveStorage.TryGetValue(entryId, out var softSaveStepData) && softSaveStepData is StorageStepData stepData)
        {
            return await this._storageConnector.SaveEntryAsync(entryId, StorageKeywords.StepDetails, stepData).ConfigureAwait(false);
        }

        return false;
    }
}
