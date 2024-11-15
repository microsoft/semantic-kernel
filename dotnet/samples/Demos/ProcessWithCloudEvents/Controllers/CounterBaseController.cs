// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Graph;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Process.Models;
using ProcessWithCloudEvents.Processes;
using ProcessWithCloudEvents.Processes.Steps;

namespace ProcessWithCloudEvents.Controllers;
public abstract class CounterBaseController : ControllerBase
{
    internal Kernel Kernel { get; init; }
    internal KernelProcess Process { get; init; }

    private static readonly JsonSerializerOptions s_jsonOptions = new()
    {
        WriteIndented = true,
        DefaultIgnoreCondition = System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingNull
    };

    internal Kernel BuildKernel(GraphServiceClient? graphClient = null)
    {
        var builder = Kernel.CreateBuilder();
        if (graphClient != null)
        {
            builder.Services.AddSingleton<GraphServiceClient>(graphClient);
        }
        return builder.Build();
    }

    internal KernelProcess InitializeProcess(ProcessBuilder process)
    {
        this.InitializeStateFile(process.Name);
        var processState = this.LoadProcessState(process.Name);
        return process.Build(processState);
    }

    private string GetTemporaryProcessFilePath(string processName)
    {
        return Path.Combine(Path.GetTempPath(), $"{processName}.json");
    }

    internal void InitializeStateFile(string processName)
    {
        // Initialize the path for the temporary file  
        var tempProcessFile = this.GetTemporaryProcessFilePath(processName);

        // If the file does not exist, create it and initialize with zero  
        if (!System.IO.File.Exists(tempProcessFile))
        {
            System.IO.File.WriteAllText(tempProcessFile, "");
        }
    }

    internal void SaveProcessState(string processName, KernelProcessStateMetadata processStateInfo)
    {
        var content = JsonSerializer.Serialize<KernelProcessStateMetadata>(processStateInfo, s_jsonOptions);
        System.IO.File.WriteAllText(this.GetTemporaryProcessFilePath(processName), content);
    }

    internal KernelProcessStateMetadata? LoadProcessState(string processName)
    {
        try
        {
            using StreamReader reader = new(this.GetTemporaryProcessFilePath(processName));
            var content = reader.ReadToEnd();
            return JsonSerializer.Deserialize<KernelProcessStateMetadata>(content, s_jsonOptions);
        }
        catch (Exception)
        {
            return null;
        }
    }

    internal void StoreProcessState(KernelProcess process)
    {
        var stateMetadata = process.ToProcessStateMetadata();
        this.SaveProcessState(process.State.Name, stateMetadata);
    }

    internal KernelProcessStepState<CounterStepState>? GetCounterState(KernelProcess process)
    {
        // TODO: Replace when there is a better way of extracting snapshot of local state
        return process.Steps
            .First(step => step.State.Name == RequestCounterProcess.StepNames.Counter).State as KernelProcessStepState<CounterStepState>;
    }

    internal async Task<KernelProcess> StartProcessWithEventAsync(string eventName, object? eventData = null)
    {
        var runningProcess = await this.Process.StartAsync(this.Kernel, new() { Id = eventName, Data = eventData });
        var processState = await runningProcess.GetStateAsync();
        this.StoreProcessState(processState);

        return processState;
    }

    public virtual async Task<int> IncreaseCounterAsync()
    {
        return await Task.FromResult(0);
    }

    public virtual async Task<int> DecreaseCounterAsync()
    {
        return await Task.FromResult(0);
    }
}
