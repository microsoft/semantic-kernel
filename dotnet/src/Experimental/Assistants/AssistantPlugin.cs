// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Linq;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

/// <summary>
/// $$$
/// </summary>
public class AssistantPlugin
{
    private readonly IAssistant _assistant;
    private readonly IChatThread _chatThread;

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="assistant"></param>
    /// <param name="thread"></param>
    public AssistantPlugin(IAssistant assistant, IChatThread thread)
    {
        this._assistant = assistant;
        this._chatThread = thread;
    }

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="message"></param>
    /// <returns></returns>
    [SKFunction, Description("Have an assistant process a message")]
    public async Task<string> InvokeAssistantAsync(
        [Description("The input message for this assistant.")]
        string message)
    {
        await this._chatThread.AddUserMessageAsync(message).ConfigureAwait(false);

        var messages = await this._chatThread.InvokeAsync(this._assistant).ConfigureAwait(false);

        return string.Concat(messages.Select(m => m.Content));
    }
}
