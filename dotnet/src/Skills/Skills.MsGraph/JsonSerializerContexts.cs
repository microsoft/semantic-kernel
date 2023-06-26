// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Skills.MsGraph;
using Microsoft.SemanticKernel.Skills.MsGraph.Models;

namespace Microsoft.SemanticKernel.Text;

[JsonSourceGenerationOptions(DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull, WriteIndented = false)]
[JsonSerializable(typeof(IEnumerable<CalendarEvent>))]
[JsonSerializable(typeof(IEnumerable<EmailMessage>))]
[JsonSerializable(typeof(IEnumerable<TaskManagementTask>))]
internal sealed partial class SourceGenerationContext : JsonSerializerContext
{
    public static readonly SourceGenerationContext WithMsGraphOptions = new(MsGraphUtils.DefaultSerializerOptions);
}
