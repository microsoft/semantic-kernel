// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Memory;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Memory;

/// <summary>
/// Contains tests for the <see cref="Mem0Provider"/> class.
/// </summary>
public class Mem0ProviderTests : IDisposable
{
    // If null, all tests will be enabled
    private const string SkipReason = "Requires a Mem0 service configured";

    private readonly HttpClient _httpClient;
    private bool _disposedValue;

    public Mem0ProviderTests()
    {
        IConfigurationRoot configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<Mem0ProviderTests>()
            .Build();

        var mem0Settings = configuration.GetRequiredSection("Mem0").Get<Mem0Configuration>()!;

        this._httpClient = new HttpClient();
        this._httpClient.BaseAddress = new Uri(mem0Settings.ServiceUri);
        this._httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Token", mem0Settings.ApiKey);
    }

    [Fact(Skip = SkipReason)]
    public async Task CanAddAndRetrieveMemoriesAsync()
    {
        // Arrange
        var question = new ChatMessage(ChatRole.User, "What is my name?");
        var input = new ChatMessage(ChatRole.User, "Hello, my name is Caoimhe.");

        var sut = new Mem0Provider(this._httpClient, options: new() { ThreadId = "test-thread-id", UserId = "test-user-id", ScopeToPerOperationThreadId = true });

        await sut.ClearStoredMemoriesAsync();
        var answerBeforeAdding = await sut.ModelInvokingAsync([question]);
        Assert.DoesNotContain("Caoimhe", answerBeforeAdding.Instructions);

        // Act
        await sut.MessageAddingAsync("test-thread-id", input);

        await sut.MessageAddingAsync("test-thread-id", question);
        var answerAfterAdding = await sut.ModelInvokingAsync([question]);

        await sut.ClearStoredMemoriesAsync();
        var answerAfterClearing = await sut.ModelInvokingAsync([question]);

        // Assert
        Assert.Contains("Caoimhe", answerAfterAdding.Instructions);
        Assert.DoesNotContain("Caoimhe", answerAfterClearing.Instructions);
    }

    [Fact(Skip = SkipReason)]
    public async Task CanAddAndRetrieveAgentMemoriesAsync()
    {
        // Arrange
        var question = new ChatMessage(ChatRole.User, "What is your name?");
        var input = new ChatMessage(ChatRole.Assistant, "Hello, I'm a friendly assistant and my name is Caoimhe.");

        var sut = new Mem0Provider(this._httpClient, options: new() { AgentId = "test-agent-id" });

        await sut.ClearStoredMemoriesAsync();
        var answerBeforeAdding = await sut.ModelInvokingAsync([question]);
        Assert.DoesNotContain("Caoimhe", answerBeforeAdding.Instructions);

        // Act
        await sut.MessageAddingAsync("test-thread-id", input);

        await sut.MessageAddingAsync("test-thread-id", question);
        var answerAfterAdding = await sut.ModelInvokingAsync([question]);

        await sut.ClearStoredMemoriesAsync();
        var answerAfterClearing = await sut.ModelInvokingAsync([question]);

        // Assert
        Assert.Contains("Caoimhe", answerAfterAdding.Instructions);
        Assert.DoesNotContain("Caoimhe", answerAfterClearing.Instructions);
    }

    [Fact(Skip = SkipReason)]
    public async Task DoesNotLeakMessagesAcrossScopesAsync()
    {
        // Arrange
        var question = new ChatMessage(ChatRole.User, "What is your name?");
        var input = new ChatMessage(ChatRole.Assistant, "I'm an AI tutor with a personality. My name is Caoimhe.");

        var sut1 = new Mem0Provider(this._httpClient, options: new() { AgentId = "test-agent-id-1" });
        var sut2 = new Mem0Provider(this._httpClient, options: new() { AgentId = "test-agent-id-2" });

        await sut1.ClearStoredMemoriesAsync();
        await sut2.ClearStoredMemoriesAsync();

        var answerBeforeAdding1 = await sut1.ModelInvokingAsync([question]);
        var answerBeforeAdding2 = await sut2.ModelInvokingAsync([question]);
        Assert.DoesNotContain("Caoimhe", answerBeforeAdding1.Instructions);
        Assert.DoesNotContain("Caoimhe", answerBeforeAdding2.Instructions);

        // Act
        await sut1.MessageAddingAsync("test-thread-id-1", input);
        var answerAfterAdding = await sut1.ModelInvokingAsync([question]);

        await sut2.MessageAddingAsync("test-thread-id-2", question);
        var answerAfterAddingOnOtherScope = await sut2.ModelInvokingAsync([question]);

        // Assert
        Assert.Contains("Caoimhe", answerAfterAdding.Instructions);
        Assert.DoesNotContain("Caoimhe", answerAfterAddingOnOtherScope.Instructions);

        // Cleanup.
        await sut1.ClearStoredMemoriesAsync();
        await sut2.ClearStoredMemoriesAsync();
    }

    [Fact(Skip = SkipReason)]
    public async Task DoesNotWorkWithMultiplePerOperationThreadsAsync()
    {
        // Arrange
        var input = new ChatMessage(ChatRole.User, "Hello, my name is Caoimhe.");

        var sut = new Mem0Provider(this._httpClient, options: new() { UserId = "test-user-id", ScopeToPerOperationThreadId = true });

        await sut.ClearStoredMemoriesAsync();

        // Act & Assert
        await sut.ConversationCreatedAsync("test-thread-id-1");
        await Assert.ThrowsAsync<InvalidOperationException>(() => sut.ConversationCreatedAsync("test-thread-id-2"));

        await sut.MessageAddingAsync("test-thread-id-1", input);
        await Assert.ThrowsAsync<InvalidOperationException>(() => sut.MessageAddingAsync("test-thread-id-2", input));

        // Cleanup
        await sut.ClearStoredMemoriesAsync();
    }

    protected virtual void Dispose(bool disposing)
    {
        if (!this._disposedValue)
        {
            if (disposing)
            {
                this._httpClient.Dispose();
            }

            this._disposedValue = true;
        }
    }

    public void Dispose()
    {
        this.Dispose(disposing: true);
        GC.SuppressFinalize(this);
    }
}
