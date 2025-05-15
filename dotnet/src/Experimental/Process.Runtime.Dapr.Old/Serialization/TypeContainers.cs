// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using Microsoft.SemanticKernel.Process.Runtime;

namespace Microsoft.SemanticKernel.Process.Serialization;

/// <summary>
/// Container for an event with type information.
/// </summary>
/// <typeparam name="TValue">The type of event</typeparam>
/// <param name="DataTypeName">The typeof the Data property</param>
/// <param name="Payload">The source event</param>
internal sealed record EventContainer<TValue>(string? DataTypeName, TValue Payload);

/// <summary>
/// Container for an message with type information.
/// </summary>
/// <param name="DataTypeName">The type of <see cref="ProcessMessage.TargetEventData"/>.</param>
/// <param name="ValueTypeNames">A type map for <see cref="ProcessMessage.Values"/>.</param>
/// <param name="Message">The source message</param>
internal sealed record MessageContainer(string? DataTypeName, Dictionary<string, string?> ValueTypeNames, ProcessMessage Message);
