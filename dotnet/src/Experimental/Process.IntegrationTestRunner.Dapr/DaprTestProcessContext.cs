// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http.Json;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Process;
using Microsoft.SemanticKernel.Process.Internal;
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
    /// <param name="runId"></param>
    /// <param name="httpClient"></param>
    internal DaprTestProcessContext(KernelProcess process, string runId, HttpClient httpClient)
    {
        Verify.NotNull(process);
        Verify.NotNullOrWhiteSpace(runId);
        Verify.NotNull(httpClient);

        this._key = process.State.StepId;
        this._processId = process.State.StepId;
        this._process = process;
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
        IDictionary<string, KernelProcessStepState> stepStates = await this.GetStepStatesAsync();

        // Build the process with the new state
        List<KernelProcessStepInfo> kernelProcessSteps = [];

        foreach (var step in this._process.Steps)
        {
            kernelProcessSteps.Add(step with { State = stepStates[step.State.StepId] });
        }

        return this._process with { Steps = kernelProcessSteps };
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

    public override async Task<IDictionary<string, KernelProcessStepState>> GetStepStatesAsync()
    {
        var response = await this._httpClient.GetStringAsync($"http://localhost:5200/processes/{this._processId}/stepStates");

        try
        {
            Dictionary<string, KernelProcessStepState> dict = new();
            using var document = JsonDocument.Parse(response);
            JsonElement root = document.RootElement;
            if (root.ValueKind != JsonValueKind.Object)
            {
                throw new InvalidOperationException("Incorrect format of States response.");
            }

            // Iterate through each property in the root object
            foreach (JsonProperty property in root.EnumerateObject())
            {
                string key = property.Name;
                JsonElement valueElement = property.Value;

                // Extract the raw JSON text for this property value
                string valueJson = RemoveStateTypeProperty(valueElement);

                // Get the associated process step
                var step = this._process!.Steps.Where(s => s.State.StepId == key).Single();
                var stateType = step.InnerStepType.ExtractStateType(out Type? userStateType, null);

                // Determine the state type and deserialize accordingly
                KernelProcessStepState? stepState = JsonSerializer.Deserialize(valueJson, stateType) as KernelProcessStepState;

                dict.Add(key, stepState);
            }

            return dict;
        }
        catch (Exception)
        {
            throw;
        }
    }

    private static string RemoveStateTypeProperty(JsonElement element)
    {
        using (var stream = new System.IO.MemoryStream())
        {
            using (var writer = new Utf8JsonWriter(stream))
            {
                writer.WriteStartObject();

                foreach (JsonProperty property in element.EnumerateObject())
                {
                    // Skip the $state-type property
                    if (property.Name == "$state-type")
                    {
                        continue;
                    }

                    property.WriteTo(writer);
                }

                writer.WriteEndObject();
            }

            return System.Text.Encoding.UTF8.GetString(stream.ToArray());
        }
    }
}
