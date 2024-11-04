// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Process.Serialization;

/// <summary>
/// %%% COMMENT
/// </summary>
/// <typeparam name="TValue"></typeparam>
/// <param name="DataType"></param>
/// <param name="Payload"></param>
internal sealed record EventContainer<TValue>(TypeInfo? DataType, TValue Payload);
