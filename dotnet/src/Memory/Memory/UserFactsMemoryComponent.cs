// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.ComponentModel;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Agents.Memory;

/// <summary>
/// A memory component that can retrieve, maintain and store user facts that
/// are learned from the user's interactions with the agent.
/// </summary>
public class UserFactsMemoryComponent : ConversationStateExtension
{
    private readonly Kernel _kernel;
    private readonly TextMemoryStore _textMemoryStore;
    private string _userFacts = string.Empty;
    private bool _contextLoaded = false;

    /// <summary>
    /// Initializes a new instance of the <see cref="UserFactsMemoryComponent"/> class.
    /// </summary>
    /// <param name="kernel">A kernel to use for making chat completion calls.</param>
    /// <param name="textMemoryStore">The memory store to retrieve and save memories from and to.</param>
    public UserFactsMemoryComponent(Kernel kernel, TextMemoryStore textMemoryStore)
    {
        this._kernel = kernel;
        this._textMemoryStore = textMemoryStore;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="UserFactsMemoryComponent"/> class.
    /// </summary>
    /// <param name="kernel">A kernel to use for making chat completion calls.</param>
    /// <param name="userFactsStoreName">The service key that the <see cref="TextMemoryStore"/> for user facts is registered under in DI.</param>
    public UserFactsMemoryComponent(Kernel kernel, string? userFactsStoreName = "UserFactsStore")
    {
        this._kernel = kernel;
        this._textMemoryStore = new OptionalTextMemoryStore(kernel, userFactsStoreName);
    }

    /// <summary>
    /// Gets or sets the name of the document to use for storing user preferfactsences.
    /// </summary>
    public string UserFactsDocumentName { get; init; } = "UserFacts";

    /// <summary>
    /// Gets or sets the prompt template to use for extracting user facts and merging them with existing facts.
    /// </summary>
    public string MaintainencePromptTemplate { get; init; } =
        """
        You are an expert in extracting facts about a user from text and combining these facts with existing facts to output a new list of facts.
        Facts are short statements that each contain a single piece of information.
        Facts should always be about the user and should always be in the present tense.
        Facts should focus on the user's long term preferences and characteristics, not on their short term actions.

        Here are 5 few shot examples:

        EXAMPLES START

        Input text: My name is John. I love dogs and cats, but unfortunately I am allergic to cats. I'm not alergic to dogs though. I have a dog called Fido.
        Input facts: User name is John. User is alergic to cats.
        Output: User name is John. User loves dogs. User loves cats. User is alergic to cats. User is not alergic to dogs. User has a dog. User dog's name is Fido.

        Input text: My name is Mary. I like active holidays. I enjoy cycling and hiking.
        Input facts: User name is Mary. User dislikes cycling.
        Output: User name is Mary. User likes cycling. User likes hiking. User likes active holidays.

        Input text: How do I calculate the area of a circle?
        Input facts:
        Output:

        Input text: What is today's date?
        Input facts: User name is Peter.
        Output: User name is Peter.

        EXAMPLES END

        Return output for the following inputs like shown in the examples above:

        Input text: {{$inputText}}
        Input facts: {{existingFacts}}
        """;

    /// <inheritdoc/>
    public override async Task OnThreadCreatedAsync(string? threadId, CancellationToken cancellationToken = default)
    {
        if (!this._contextLoaded)
        {
            this._userFacts = string.Empty;

            var memoryText = await this._textMemoryStore.GetMemoryAsync(this.UserFactsDocumentName, cancellationToken).ConfigureAwait(false);
            if (memoryText is not null)
            {
                this._userFacts = memoryText;
            }

            this._contextLoaded = true;
        }
    }

    /// <inheritdoc/>
    public override async Task OnThreadDeleteAsync(string? threadId, CancellationToken cancellationToken = default)
    {
        await this._textMemoryStore.SaveMemoryAsync(this.UserFactsDocumentName, this._userFacts, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public override async Task OnNewMessageAsync(ChatMessageContent newMessage, CancellationToken cancellationToken = default)
    {
        if (newMessage.Role == AuthorRole.User && !string.IsNullOrWhiteSpace(newMessage.Content))
        {
            // Don't wait for task to complete. Just run in the background.
            await this.ExtractAndSaveMemoriesAsync(newMessage.Content, cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    public override Task<string> OnAIInvocationAsync(ICollection<ChatMessageContent> newMessages, CancellationToken cancellationToken = default)
    {
        return Task.FromResult("The following list contains facts about the user:\n" + this._userFacts);
    }

    /// <inheritdoc/>
    public override void RegisterPlugins(Kernel kernel)
    {
        Verify.NotNull(kernel);

        base.RegisterPlugins(kernel);
        kernel.Plugins.AddFromObject(this, "UserFactsMemory");
    }

    /// <inheritdoc/>
    public override Task OnResumeAsync(string? threadId, CancellationToken cancellationToken = default)
    {
        return this.OnThreadCreatedAsync(threadId, cancellationToken);
    }

    /// <inheritdoc/>
    public override Task OnSuspendAsync(string? threadId, CancellationToken cancellationToken = default)
    {
        return this.OnThreadDeleteAsync(threadId, cancellationToken);
    }

    /// <summary>
    /// Plugin method to clear user facts stored in memory.
    /// </summary>
    [KernelFunction]
    [Description("Deletes any user facts stored about the user.")]
    public async Task ClearUserFactsAsync(CancellationToken cancellationToken = default)
    {
        this._userFacts = string.Empty;
        await this._textMemoryStore.SaveMemoryAsync(this.UserFactsDocumentName, this._userFacts, cancellationToken).ConfigureAwait(false);
    }

    private async Task ExtractAndSaveMemoriesAsync(string inputText, CancellationToken cancellationToken = default)
    {
        var result = await this._kernel.InvokePromptAsync(
            this.MaintainencePromptTemplate,
            new KernelArguments() { ["inputText"] = inputText, ["existingFacts"] = this._userFacts },
            cancellationToken: cancellationToken).ConfigureAwait(false);

        this._userFacts = result.ToString();

        await this._textMemoryStore.SaveMemoryAsync(this.UserFactsDocumentName, this._userFacts, cancellationToken).ConfigureAwait(false);
    }
}
