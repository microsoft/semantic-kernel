// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using Microsoft.SemanticKernel.Process.Runtime;

namespace Microsoft.SemanticKernel.Process.Serialization;

/// <summary>
/// %%% COMMENT
/// </summary>
/// <typeparam name="TValue"></typeparam>
/// <param name="DataTypeName"></param>
/// <param name="Payload"></param>
internal sealed record EventContainer<TValue>(string? DataTypeName, TValue Payload);

/// <summary>
/// %%% COMMENT
/// </summary>
/// <param name="DataTypeName"></param>
/// <param name="ValueTypeNames"></param>
/// <param name="Message"></param>
internal sealed record MessageContainer(string? DataTypeName, Dictionary<string, string?> ValueTypeNames, ProcessMessage Message);
