// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Plugins.AI.CrewAI;

#pragma warning disable CA1812 // Avoid uninstantiated internal classes
internal sealed class CrewAIStateEnumConverter : JsonConverter<CrewAIKickoffState>
{
    public override CrewAIKickoffState Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        string? stringValue = reader.GetString();
        return stringValue?.ToUpperInvariant() switch
        {
            "PENDING" => CrewAIKickoffState.Pending,
            "STARTED" => CrewAIKickoffState.Started,
            "RUNNING" => CrewAIKickoffState.Running,
            "SUCCESS" => CrewAIKickoffState.Success,
            "FAILED" => CrewAIKickoffState.Failed,
            "FAILURE" => CrewAIKickoffState.Failure,
            "NOT FOUND" => CrewAIKickoffState.NotFound,
            _ => throw new KernelException("Failed to parse Crew AI kickoff state.")
        };
    }

    public override void Write(Utf8JsonWriter writer, CrewAIKickoffState value, JsonSerializerOptions options)
    {
        string stringValue = value switch
        {
            CrewAIKickoffState.Pending => "PENDING",
            CrewAIKickoffState.Started => "STARTED",
            CrewAIKickoffState.Running => "RUNNING",
            CrewAIKickoffState.Success => "SUCCESS",
            CrewAIKickoffState.Failed => "FAILED",
            CrewAIKickoffState.Failure => "FAILURE",
            CrewAIKickoffState.NotFound => "NOT FOUND",
            _ => throw new KernelException("Failed to parse Crew AI kickoff state.")
        };
        writer.WriteStringValue(stringValue);
    }
}
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
