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

    private string GetStepEntryId(KernelProcessStepInfo step)
    {
        Verify.NotNullOrWhiteSpace(step.StepId);
        Verify.NotNullOrWhiteSpace(step.RunId);

        return $"{this.GetEntryId(step.StepId, step.RunId)}.{StorageKeywords.StepDetails}";
        //return step.RunId;
    }

    /// <summary>
    /// Get process data from storage
    /// </summary>
    /// <param name="process"></param>
    /// <returns></returns>
    public async Task FetchProcessDataAsync(KernelProcess process)
    {
        var entryId = this.GetProcessEntryId(process);

        var storageState = await this._storageConnector.GetEntryAsync<StorageProcessData>(entryId).ConfigureAwait(false);
        if (storageState != null)
        {
            this._softSaveStorage[entryId] = storageState;
        }
    }

    public async Task<StorageProcessInfo?> GetProcessInfoAsync(KernelProcess process)
    {
        var entryId = this.GetProcessEntryId(process);
        if (this._softSaveStorage.TryGetValue(entryId, out var softSaveProcessData) && softSaveProcessData is StorageProcessData processData)
        {
            return processData.ProcessInfo;
        }
        return null;
    }

    /// <summary>
    /// Save process data to storage
    /// </summary>
    /// <param name="process"></param>
    /// <returns></returns>
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

    /// <summary>
    /// To be called when process data is already saved in soft save storage and needs to be saved to the actual storage.
    /// Should be called at the end of each super step in a process run.
    /// </summary>
    /// <param name="process"></param>
    /// <returns></returns>
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

    /// <summary>
    /// Fetches all step data related info like state, messages, info from the cloud and stores it locally
    /// </summary>
    /// <param name="step"></param>
    /// <returns></returns>
    public async Task FetchStepDataAsync(KernelProcessStepInfo step)
    {
        var entryId = this.GetStepEntryId(step);
        var storageState = await this._storageConnector.GetEntryAsync<StorageStepData>(entryId).ConfigureAwait(false);

        if (storageState != null)
        {
            this._softSaveStorage[entryId] = storageState;
        }
    }

    public async Task<StorageStepInfo?> GetStepInfoAsync(KernelProcessStepInfo step)
    {
        var entryId = this.GetStepEntryId(step);
        if (this._softSaveStorage.TryGetValue(entryId, out var softSaveStepData) && softSaveStepData is StorageStepData stepData)
        {
            return stepData.StepInfo;
        }
        return null;
    }

    /// <summary>
    /// Save step data to storage
    /// </summary>
    /// <param name="step"></param>
    /// <returns></returns>
    public async Task<bool> SaveStepInfoAsync(KernelProcessStepInfo step)
    {
        Verify.NotNullOrWhiteSpace(step.RunId);

        var entryId = this.GetStepEntryId(step);
        if (!this._softSaveStorage.TryGetValue(entryId, out var stepSavedData))
        {
            stepSavedData = new StorageStepData() { InstanceId = step.RunId };
            this._softSaveStorage.TryAdd(entryId, stepSavedData);
        }

        if (stepSavedData is StorageStepData stepData)
        {
            stepData.StepInfo = step.ToStorageStepInfo();
        }

        return true;
    }

    /// <summary>
    /// Get step state data from storage
    /// </summary>
    /// <param name="step"></param>
    /// <returns></returns>
    public async Task<KernelProcessStepState?> GetStepStateAsync(KernelProcessStepInfo step)
    {
        var entryId = this.GetStepEntryId(step);
        if (this._softSaveStorage.TryGetValue(entryId, out var softSaveStepData) && softSaveStepData is StorageStepData stepData)
        {
            return stepData.ToKernelProcessStepState();
        }

        return null;
    }

    public async Task<bool> SaveStepStateAsync(KernelProcessStepInfo step)
    {
        Verify.NotNullOrWhiteSpace(step.RunId);

        var entryId = this.GetStepEntryId(step);

        if (!this._softSaveStorage.TryGetValue(entryId, out var stepSavedData))
        {
            stepSavedData = new StorageStepData() { InstanceId = step.RunId };
            this._softSaveStorage.TryAdd(entryId, stepSavedData);
        }

        if (stepSavedData is StorageStepData stepData)
        {
            stepData.StepState = step.ToStorageStepState();
        }

        return true;
    }

    public async Task<StorageStepEvents?> GetStepEventsAsync(KernelProcessStepInfo step)
    {
        var entryId = this.GetStepEntryId(step);
        if (this._softSaveStorage.TryGetValue(entryId, out var softSaveStepData) && softSaveStepData is StorageStepData stepData)
        {
            return stepData.StepEvents;
        }

        return null;
    }

    public async Task<bool> SaveStepEventsAsync(KernelProcessStepInfo step, Dictionary<string, Dictionary<string, object?>>? edgeGroups = null)
    {
        Verify.NotNullOrWhiteSpace(step.RunId);
        var entryId = this.GetStepEntryId(step);

        if (!this._softSaveStorage.TryGetValue(entryId, out var stepSavedData))
        {
            stepSavedData = new StorageStepData() { InstanceId = step.RunId };
            this._softSaveStorage.TryAdd(entryId, stepSavedData);
        }
        if (stepSavedData is StorageStepData stepData)
        {
            stepData.StepEvents = step.ToStorageStepEvents(edgeGroups);
        }
        return true;
    }

    public async Task<bool> SaveStepDataToStorageAsync(KernelProcessStepInfo step)
    {
        var entryId = this.GetStepEntryId(step);
        if (this._softSaveStorage.TryGetValue(entryId, out var softSaveStepData) && softSaveStepData is StorageStepData stepData)
        {
            return await this._storageConnector.SaveEntryAsync(entryId, StorageKeywords.StepDetails, stepData).ConfigureAwait(false);
        }

        return false;
    }
}
