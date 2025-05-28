// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http.Json;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Process;
using Microsoft.SemanticKernel.Process.Serialization;
using SemanticKernel.Process.TestsShared.CloudEvents;

namespace SemanticKernel.Process.IntegrationTests;
internal sealed class DaprTestProcessContext : KernelProcessContext
{
    private readonly HttpClient _httpClient;
    private readonly KernelProcess? _process;
    private readonly string? _key;
    private readonly string _processId;
    private readonly JsonSerializerOptions _serializerOptions;

    /// <summary>
    /// Creates a new instance of the <see cref="DaprTestProcessContext"/> class.
    /// </summary>
    /// <param name="process"></param>
    /// <param name="httpClient"></param>
    internal DaprTestProcessContext(KernelProcess process, HttpClient httpClient)
    {
        if (string.IsNullOrWhiteSpace(process.State.RunId))
        {
            process = process with { State = process.State with { RunId = Guid.NewGuid().ToString() } };
        }

        this._process = process;
        this._processId = process.State.RunId;
        this._httpClient = httpClient;

        this._serializerOptions = new JsonSerializerOptions()
        {
            TypeInfoResolver = new ProcessStateTypeResolver<KickoffStep>(),
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase
        };
    }

    /// <summary>
    /// Creates a new instance of the <see cref="DaprTestProcessContext"/> class.
    /// </summary>
    /// <param name="key"></param>
    /// <param name="id"></param>
    /// <param name="httpClient"></param>
    internal DaprTestProcessContext(string key, string id, HttpClient httpClient)
    {
        Verify.NotNullOrWhiteSpace(key);
        Verify.NotNullOrWhiteSpace(id);
        Verify.NotNull(httpClient);

        this._key = key;
        this._processId = id;
        this._httpClient = httpClient;

        this._serializerOptions = new JsonSerializerOptions()
        {
            TypeInfoResolver = new ProcessStateTypeResolver<KickoffStep>(),
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase
        };
    }

    /// <summary>
    /// Starts the process with an initial event.
    /// </summary>
    /// <param name="initialEvent">The initial event.</param>
    /// <returns></returns>
    internal async Task StartWithEventAsync(KernelProcessEvent initialEvent)
    {
        if (this._process is null)
        {
            throw new InvalidOperationException("Process is not set");
        }

        try
        {
            var daprProcess = DaprProcessInfo.FromKernelProcess(this._process);
            var request = new ProcessStartRequest { Process = daprProcess, InitialEvent = initialEvent.ToJson() };

            var response = await this._httpClient.PostAsJsonAsync($"http://localhost:5200/processes/{this._processId}", request, options: this._serializerOptions).ConfigureAwait(false);
            if (!response.IsSuccessStatusCode)
            {
                throw new InvalidOperationException("Failed to start process");
            }
        }
        catch (Exception)
        {
            throw;
        }
    }

    /// <summary>
    /// Starts the process with an initial event.
    /// </summary>
    /// <param name="id">The process id.</param>
    /// <param name="initialEvent">The initial event.</param>
    /// <returns></returns>
    internal async Task StartKeyedWithEventAsync(string id, KernelProcessEvent initialEvent)
    {
        Verify.NotNullOrWhiteSpace(id);
        Verify.NotNull(initialEvent);

        if (this._key is null)
        {
            throw new InvalidOperationException("Key is not set");
        }

        var request = new ProcessStartRequest { InitialEvent = initialEvent.ToJson() };

        var response = await this._httpClient.PostAsJsonAsync($"http://localhost:5200/processes/{this._key}/{this._processId}", request, options: this._serializerOptions).ConfigureAwait(false);
        if (!response.IsSuccessStatusCode)
        {
            throw new InvalidOperationException("Failed to start process");
        }
    }

    public override async Task<KernelProcess> GetStateAsync()
    {
        var response = await this._httpClient.GetFromJsonAsync<DaprProcessInfo>($"http://localhost:5200/processes/{this._processId}", options: this._serializerOptions);
        return response switch
        {
            null => throw new InvalidOperationException("Process not found"),
            _ => response.ToKernelProcess()
        };
    }

    public override Task SendEventAsync(KernelProcessEvent processEvent)
    {
        throw new NotImplementedException();
    }

    public override Task StopAsync()
    {
        throw new NotImplementedException();
    }

    public override async Task<IExternalKernelProcessMessageChannel?> GetExternalMessageChannelAsync()
    {
        var response = await this._httpClient.GetFromJsonAsync<MockCloudEventClient>($"http://localhost:5200/processes/{this._processId}/mockCloudClient", options: this._serializerOptions);
        return response switch
        {
            null => throw new InvalidOperationException("Process not found"),
            _ => response
        };
    }

    public override Task<string> GetProcessIdAsync() => Task.FromResult(this._process?.State.RunId!);
}
