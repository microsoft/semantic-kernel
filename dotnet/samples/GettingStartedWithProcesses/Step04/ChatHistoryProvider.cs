// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Step04;

/// <summary>
/// %%%
/// </summary>
internal interface IChatHistoryProvider
{
    /// <summary>
    /// %%%
    /// </summary>
    /// <returns></returns>
    ChatHistory GetHistory();
}

/// <summary>
/// %%%
/// </summary>
internal sealed class ChatHistoryProvider(ChatHistory history) : IChatHistoryProvider
{
    /// <inheritdoc/>
    public ChatHistory GetHistory() => history;
}

internal static class KernelExtensionsForHistoryProvider
{
    public static ChatHistory GetHistory(this Kernel kernel) => kernel.GetRequiredService<IChatHistoryProvider>().GetHistory();
}
