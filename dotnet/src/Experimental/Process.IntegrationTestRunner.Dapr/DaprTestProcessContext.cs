// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http.Json;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Process;

namespace SemanticKernel.Process.IntegrationTests;
internal class DaprTestProcessContext : KernelProcessContext
{
    private readonly HttpClient _httpClient;
    private readonly KernelProcess _process;
    private readonly string _processId;
    private readonly JsonSerializerOptions _serializerOptions;

    internal DaprTestProcessContext(KernelProcess process, HttpClient httpClient)
    {
        if (string.IsNullOrWhiteSpace(process.State.Id))
        {
            process = process with { State = process.State with { Id = Guid.NewGuid().ToString() } };
        }

        this._process = process;
        this._processId = process.State.Id;
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
        try
        {
            var daprProcess = DaprProcessInfo.FromKernelProcess(this._process);
            var request = new ProcessStartRequest { Process = daprProcess, InitialEvent = initialEvent };

            var response = await this._httpClient.PostAsJsonAsync($"http://localhost:5200/processes/{this._processId}/start", request, options: this._serializerOptions).ConfigureAwait(false);
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

    public override async Task<KernelProcess> GetStateAsync()
    {
        var response = await this._httpClient.GetAsync(new Uri($"http://localhost:5200/processes/{this._processId}"));
        if (!response.IsSuccessStatusCode)
        {
            throw new InvalidOperationException("Failed to retrieve process.");
        }

        var stringRes = await response.Content.ReadAsStringAsync();
        var daprProcess = JsonSerializer.Deserialize<DaprProcessInfo>(stringRes, options: this._serializerOptions);
        if (daprProcess == null)
        {
            throw new InvalidOperationException("Failed to retrieve process.");
        }

        return daprProcess.ToKernelProcess();
    }

    public override Task SendEventAsync(KernelProcessEvent processEvent)
    {
        throw new NotImplementedException();
    }

    public override Task StopAsync()
    {
        throw new NotImplementedException();
    }
}
