// Copyright (c) Microsoft. All rights reserved.
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

#pragma warning disable SYSLIB1006 // Multiple logging methods cannot use the same event id within a class

/// <summary>
/// Extensions for logging <see cref="AggregatorAgent"/> invocations.
/// </summary>
/// <remarks>
/// This extension uses the <see cref="LoggerMessageAttribute"/> to
/// generate logging code at compile time to achieve optimized code.
/// </remarks>
internal static partial class OpenAIAssistantChannelLogMessages
{
}
