// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Process.Internal;
using Microsoft.SemanticKernel.Process.Models;
using Microsoft.SemanticKernel.Process.Models.Storage;

namespace Microsoft.SemanticKernel.Process;

/// <summary>
/// Storage manager for storing step and process related data using the implementation of <see cref="IProcessStorageConnector"/>.
/// </summary>
public class ProcessStorageManager
{
    internal static class StorageKeywords
    {
        // Suffixes
        public const string ParentProcess = nameof(ParentProcess);
        // Types
        public const string ProcessState = nameof(ProcessState);
        public const string StepState = nameof(StepState);

        public const string StepEdgesData = nameof(StepEdgesData);
    }

    private readonly IProcessStorageConnector _storageConnector;

    private bool _isInitialized = false;

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

    private string GetParentId(string componentName, string componentId)
    {
        return $"{this.GetEntryId(componentName, componentId)}.{StorageKeywords.ParentProcess}";
    }

    private string GetStepStateId(string componentName, string componentId)
    {
        return $"{this.GetEntryId(componentName, componentId)}.{StorageKeywords.StepState}";
    }

    private string GetProcessStateId(string componentName, string componentId)
    {
        return $"{this.GetEntryId(componentName, componentId)}.{StorageKeywords.ProcessState}";
    }

    private string GetStepEdgesId(string componentName, string componentId)
    {
        return $"{this.GetEntryId(componentName, componentId)}.{StorageKeywords.StepEdgesData}";
    }

    /// <summary>
    /// Get process data from storage
    /// </summary>
    /// <param name="processName"></param>
    /// <param name="processId"></param>
    /// <returns></returns>
    public async Task<StorageProcessState?> GetProcessDataAsync(string processName, string processId)
    {
        var entryId = this.GetProcessStateId(processName, processId);
        return await this._storageConnector.GetEntryAsync<StorageProcessState>(entryId).ConfigureAwait(false);
    }

    /// <summary>
    /// Save process data to storage
    /// </summary>
    /// <param name="processName"></param>
    /// <param name="processId"></param>
    /// <param name="state"></param>
    /// <returns></returns>
    public async Task<bool> SaveProcessDataAsync(string processName, string processId, KernelProcess state)
    {
        var entryId = this.GetProcessStateId(processName, processId);
        return await this._storageConnector.SaveEntryAsync(entryId, StorageKeywords.ProcessState, state.ToKernelStorageProcessState()).ConfigureAwait(false);
    }

    /// <summary>
    /// Get step state data from storage
    /// </summary>
    /// <param name="stepName"></param>
    /// <param name="stepId"></param>
    /// <returns></returns>
    public async Task<KernelProcessStepStateMetadata?> GetStepDataAsync(string stepName, string stepId)
    {
        var entryId = this.GetStepStateId(stepName, stepId);
        var data = await this._storageConnector.GetEntryAsync<StorageStepState>(entryId).ConfigureAwait(false);
        return data?.ToKernelStepMetadata();
    }

    /// <summary>
    /// Save step state data to storage
    /// </summary>
    /// <param name="stepName"></param>
    /// <param name="stepId"></param>
    /// <param name="state"></param>
    /// <returns></returns>
    public async Task<bool> SaveStepStateDataAsync(string stepName, string stepId, KernelProcessStepStateMetadata state)
    {
        var entryId = this.GetStepStateId(stepName, stepId);
        return await this._storageConnector.SaveEntryAsync(entryId, StorageKeywords.ProcessState, state.ToKernelStorageStepState()).ConfigureAwait(false);
    }

    /// <summary>
    /// Get step edge data from storage
    /// </summary>
    /// <param name="stepName"></param>
    /// <param name="stepId"></param>
    /// <returns></returns>
    public async Task<(bool, Dictionary<string, Dictionary<string, KernelProcessEventData?>>?)> GetStepEdgeDataAsync(string stepName, string stepId)
    {
        var entryId = this.GetStepEdgesId(stepName, stepId);
        var data = await this._storageConnector.GetEntryAsync<StorageStepEdgesData>(entryId).ConfigureAwait(false);
        return (data?.IsGroupEdge ?? false, data?.EdgesData);
    }

    /// <summary>
    /// Save step edge data to storage
    /// </summary>
    /// <param name="stepName"></param>
    /// <param name="stepId"></param>
    /// <param name="stepEdgesData"></param>
    /// <param name="isGroupEdge"></param>
    /// <returns></returns>
    public async Task<bool> SaveStepEdgeDataAsync(string stepName, string stepId, Dictionary<string, Dictionary<string, object?>?> stepEdgesData, bool isGroupEdge)
    {
        var entryId = this.GetStepEdgesId(stepName, stepId);
        var entryData = new StorageStepEdgesData() { EdgesData = stepEdgesData.PackStepEdgesValues() ?? [], IsGroupEdge = isGroupEdge };
        return await this._storageConnector.SaveEntryAsync(entryId, StorageKeywords.StepEdgesData, entryData).ConfigureAwait(false);
    }

    /// <summary>
    /// Get parent data from storage
    /// </summary>
    /// <param name="entityKey"></param>
    /// <param name="entityId"></param>
    /// <returns></returns>
    public async Task<StorageParentData?> GetParentDataAsync(string entityKey, string entityId)
    {
        var entryId = this.GetParentId(entityKey, entityId);
        return await this._storageConnector.GetEntryAsync<StorageParentData>(entryId).ConfigureAwait(false);
    }

    /// <summary>
    /// Save parent data to storage
    /// </summary>
    /// <param name="entityKey"></param>
    /// <param name="entityId"></param>
    /// <param name="parentData"></param>
    /// <returns></returns>
    public async Task<bool> SaveParentDataAsync(string entityKey, string entityId, StorageParentData parentData)
    {
        var entryId = this.GetParentId(entityKey, entityId);
        return await this._storageConnector.SaveEntryAsync(entryId, StorageKeywords.ParentProcess, parentData).ConfigureAwait(false);
    }
}
