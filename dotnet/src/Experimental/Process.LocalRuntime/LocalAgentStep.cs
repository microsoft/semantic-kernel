// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Process.Internal;
using Microsoft.SemanticKernel.Process.Runtime;

namespace Microsoft.SemanticKernel.Process;
internal class LocalAgentStep : LocalStep
{
    private new readonly KernelProcessAgentStep _stepInfo;
    private readonly KernelProcessAgentThread _agentThread;
    private readonly ProcessStateManager _processStateManager;
    private readonly ILogger _logger;

    public LocalAgentStep(KernelProcessAgentStep stepInfo, Kernel kernel, KernelProcessAgentThread agentThread, ProcessStateManager processStateManager, string? parentProcessId = null) : base(stepInfo, kernel, parentProcessId)
    {
        this._stepInfo = stepInfo;
        this._agentThread = agentThread;
        this._processStateManager = processStateManager;
        this._logger = this._kernel.LoggerFactory?.CreateLogger(this._stepInfo.InnerStepType) ?? new NullLogger<LocalAgentStep>();
    }

    protected override ValueTask InitializeStepAsync()
    {
        this._stepInstance = new KernelProcessAgentExecutorInternal(this._stepInfo, this._agentThread, this._processStateManager);
        var kernelPlugin = KernelPluginFactory.CreateFromObject(this._stepInstance, pluginName: this._stepInfo.State.Name);

        // Load the kernel functions
        foreach (KernelFunction f in kernelPlugin)
        {
            this._functions.Add(f.Name, f);
        }
        return default;
    }

    internal override async Task HandleMessageAsync(ProcessMessage message)
    {
        Verify.NotNull(message, nameof(message));

        // Lazy one-time initialization of the step before processing a message
        await this._initializeTask.Value.ConfigureAwait(false);

        string targetFunction = "Invoke";
        KernelArguments arguments = new() { { "message", message.TargetEventData }, { "writtenToThread", message.writtenToThread == this._agentThread.ThreadId } };
        if (!this._functions.TryGetValue(targetFunction, out KernelFunction? function) || function == null)
        {
            throw new ArgumentException($"Function Invoke not found in plugin {this.Name}");
        }

        object? result = null;

        // Invoke the function, catching all exceptions that it may throw, and then post the appropriate event.
#pragma warning disable CA1031 // Do not catch general exception types
        try
        {
            FunctionResult invokeResult = await this.InvokeFunction(function, this._kernel, arguments).ConfigureAwait(false);
            result = invokeResult.GetValue<object>();
            this.EmitEvent(
                ProcessEvent.Create(
                    result,
                    this._eventNamespace,
                    sourceId: $"{targetFunction}.OnResult",
                    eventVisibility: KernelProcessEventVisibility.Public,
                    writtenToThread: this._agentThread.ThreadId)); // TODO: This is keeping track of the thread the message has been written to, clean it up, name it better, etc. 
        }
        catch (Exception ex)
        {
            this._logger.LogError(ex, "Error in Step {StepName}: {ErrorMessage}", this.Name, ex.Message);
            var processError = KernelProcessError.FromException(ex);
            this.EmitEvent(
                ProcessEvent.Create(
                    processError,
                    this._eventNamespace,
                    sourceId: $"{targetFunction}.OnError",
                    eventVisibility: KernelProcessEventVisibility.Public,
                    isError: true));

            if (this._stepInfo.Actions.DeclarativeActions?.OnError is not null)
            {
                await this.ProcessDeclarativeConditionsAsync(processError, this._stepInfo.Actions.DeclarativeActions.OnError).ConfigureAwait(false);
            }
            if (this._stepInfo.Actions.CodeActions?.OnError is not null)
            {
                this._stepInfo.Actions.CodeActions?.OnError(processError, new KernelProcessStepContext(this));
            }

            return;
        }
#pragma warning restore CA1031 // Do not catch general exception types

        // TODO: Should these be handled within the try or out of it?
        if (this._stepInfo.Actions.DeclarativeActions?.OnComplete is not null)
        {
            await this.ProcessDeclarativeConditionsAsync(result, this._stepInfo.Actions.DeclarativeActions.OnComplete).ConfigureAwait(false);
        }
        if (this._stepInfo.Actions.CodeActions?.OnComplete is not null)
        {
            this._stepInfo.Actions.CodeActions?.OnComplete(result, new KernelProcessStepContext(this));
        }
    }

    private async Task ProcessDeclarativeConditionsAsync(object? result, KernelProcessDeclarativeConditionHandler conditionHandler)
    {
        int executedConditionCount = 0;
        foreach (var onCompleteStateCondition in conditionHandler.EvalConditions ?? [])
        {
            // process state conditions
            await this.ProcessConditionsAsync(result, onCompleteStateCondition).ConfigureAwait(false);
            executedConditionCount++;
            // Test condition
            // TODO: Apply state conditions to the result and emit events
        }

        var alwaysCondition = conditionHandler.AlwaysCondition;
        if (alwaysCondition != null)
        {
            // process semantic conditions
            await this.ProcessConditionsAsync(result, alwaysCondition).ConfigureAwait(false);
            executedConditionCount++;
            // TODO: Apply state conditions to the result and emit events
        }

        var defaultCondition = conditionHandler.DefaultCondition;
        if (executedConditionCount == 0 && defaultCondition != null)
        {
            await this.ProcessConditionsAsync(result, defaultCondition).ConfigureAwait(false);
            executedConditionCount++;
        }
    }

    private async Task ProcessConditionsAsync(object? result, DeclarativeProcessCondition declarativeCondition)
    {
        await this._processStateManager.ReduceAsync((stateType, state) =>
        {
            var stateJson = JsonDocument.Parse(JsonSerializer.Serialize(state));

            if (string.IsNullOrWhiteSpace(declarativeCondition.Expression) || JMESPathConditionEvaluator.EvaluateCondition(state, declarativeCondition.Expression))
            {
                if (declarativeCondition.Updates is not null)
                {
                    foreach (var update in declarativeCondition.Updates)
                    {
                        stateJson = this.UpdateState(stateJson, update.Path, update.Operation, update.Value);
                    }
                }

                if (declarativeCondition.Emits is not null)
                {
                    foreach (var emit in declarativeCondition.Emits)
                    {
                        this.EmitEvent(
                            ProcessEvent.Create(
                                result, // TODO: Use the correct value as defined in emit.Payload
                                this._eventNamespace,
                                sourceId: emit.EventType,
                                eventVisibility: KernelProcessEventVisibility.Public));
                    }
                }
            }

            return Task.FromResult(stateJson.Deserialize(stateType));
        }).ConfigureAwait(false);
    }

    private JsonDocument UpdateState(JsonDocument document, string path, StateUpdateOperations operation, object? value = null)
    {
        if (document == null)
        {
            throw new ArgumentNullException(nameof(document));
        }

        if (string.IsNullOrEmpty(path))
        {
            throw new ArgumentException("Path cannot be null or empty", nameof(path));
        }

        try
        {
            // Clone the document for immutability
            using var memoryStream = new MemoryStream();
            using (var jsonWriter = new Utf8JsonWriter(memoryStream))
            {
                this.UpdateJsonElement(document.RootElement, jsonWriter, path.Split('.'), 0, operation, value);
                jsonWriter.Flush();
            }

            memoryStream.Position = 0;
            return JsonDocument.Parse(memoryStream);
        }
        catch (JsonException ex)
        {
            throw new InvalidOperationException($"JSON processing error: {ex.Message}", ex);
        }
        catch (IOException ex)
        {
            throw new InvalidOperationException($"I/O error during JSON update: {ex.Message}", ex);
        }
        catch (ArgumentOutOfRangeException ex)
        {
            throw new ArgumentException($"Invalid path: {ex.Message}", ex);
        }
    }

    private void UpdateJsonElement(JsonElement element, Utf8JsonWriter writer, string[] pathParts, int depth, StateUpdateOperations operation, object? value)
    {
        // If we're at the target element
        if (depth == pathParts.Length)
        {
            this.PerformOperation(element, writer, operation, value);
            return;
        }

        // If we're at an intermediate level
        switch (element.ValueKind)
        {
            case JsonValueKind.Object:
                writer.WriteStartObject();

                foreach (var property in element.EnumerateObject())
                {
                    if (property.Name == pathParts[depth])
                    {
                        writer.WritePropertyName(property.Name);
                        this.UpdateJsonElement(property.Value, writer, pathParts, depth + 1, operation, value);
                    }
                    else
                    {
                        property.WriteTo(writer);
                    }
                }

                writer.WriteEndObject();
                break;

            case JsonValueKind.Array:
                writer.WriteStartArray();

                // Check if the path part is a valid array index
                if (int.TryParse(pathParts[depth], out int index) && index < element.GetArrayLength())
                {
                    int i = 0;
                    foreach (var item in element.EnumerateArray())
                    {
                        if (i == index)
                        {
                            this.UpdateJsonElement(item, writer, pathParts, depth + 1, operation, value);
                        }
                        else
                        {
                            item.WriteTo(writer);
                        }
                        i++;
                    }
                }
                else
                {
                    // If the index is invalid, just copy the array unchanged
                    foreach (var item in element.EnumerateArray())
                    {
                        item.WriteTo(writer);
                    }
                }

                writer.WriteEndArray();
                break;

            default:
                // We've reached a leaf node before the full path was traversed
                // Just write the current value and return
                element.WriteTo(writer);
                break;
        }
    }

    private void PerformOperation(JsonElement element, Utf8JsonWriter writer, StateUpdateOperations operation, object? value)
    {
        try
        {
            switch (operation)
            {
                case StateUpdateOperations.Set:
                    this.WriteValue(writer, value);
                    break;

                case StateUpdateOperations.Increment:
                    if (element.ValueKind != JsonValueKind.Number)
                    {
                        throw new InvalidOperationException("Cannot increment non-numeric value at the specified path");
                    }

                    if (element.TryGetInt32(out int intValue))
                    {
                        int incrementBy = value != null ? Convert.ToInt32(value) : 1;
                        writer.WriteNumberValue(intValue + incrementBy);
                    }
                    else if (element.TryGetDouble(out double doubleValue))
                    {
                        double incrementBy = value != null ? Convert.ToDouble(value) : 1.0;
                        writer.WriteNumberValue(doubleValue + incrementBy);
                    }
                    break;

                case StateUpdateOperations.Decrement:
                    if (element.ValueKind != JsonValueKind.Number)
                    {
                        throw new InvalidOperationException("Cannot decrement non-numeric value at the specified path");
                    }

                    if (element.TryGetInt32(out int intVal))
                    {
                        int decrementBy = value != null ? Convert.ToInt32(value) : 1;
                        writer.WriteNumberValue(intVal - decrementBy);
                    }
                    else if (element.TryGetDouble(out double doubleVal))
                    {
                        double decrementBy = value != null ? Convert.ToDouble(value) : 1.0;
                        writer.WriteNumberValue(doubleVal - decrementBy);
                    }
                    break;

                default:
                    throw new NotSupportedException($"Operation {operation} is not supported");
            }
        }
        catch (FormatException ex)
        {
            throw new ArgumentException($"Value format error: {ex.Message}", ex);
        }
        catch (OverflowException ex)
        {
            throw new ArgumentException($"Numeric overflow during operation: {ex.Message}", ex);
        }
    }

    private void WriteValue(Utf8JsonWriter writer, object? value)
    {
        if (value == null)
        {
            writer.WriteNullValue();
            return;
        }

        switch (value)
        {
            case string strValue:
                writer.WriteStringValue(strValue);
                break;
            case int intValue:
                writer.WriteNumberValue(intValue);
                break;
            case long longValue:
                writer.WriteNumberValue(longValue);
                break;
            case double doubleValue:
                writer.WriteNumberValue(doubleValue);
                break;
            case decimal decimalValue:
                writer.WriteNumberValue(decimalValue);
                break;
            case bool boolValue:
                writer.WriteBooleanValue(boolValue);
                break;
            case DateTime dateTimeValue:
                writer.WriteStringValue(dateTimeValue);
                break;
            default:
                // For complex objects, serialize them to JSON
                var json = JsonSerializer.Serialize(value);
                using (var doc = JsonDocument.Parse(json))
                {
                    doc.RootElement.WriteTo(writer);
                }
                break;
        }
    }
}
