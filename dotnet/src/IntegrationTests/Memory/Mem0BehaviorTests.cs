﻿// Copyright (c) Microsoft. All rights reserved.

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
/// Contains tests for the <see cref="Mem0Behavior"/> class.
/// </summary>
public class Mem0BehaviorTests : IDisposable
{
    // If null, all tests will be enabled
    private const string SkipReason = "Requires a Mem0 service configured";

    private readonly HttpClient _httpClient;
    private bool _disposedValue;

    public Mem0BehaviorTests()
    {
        IConfigurationRoot configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<Mem0BehaviorTests>()
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

        var sut = new Mem0Behavior(this._httpClient, new() { ThreadId = "test-thread-id", UserId = "test-user-id", ScopeToPerOperationThreadId = true });

        await sut.ClearStoredMemoriesAsync();
        var answerBeforeAdding = await sut.OnModelInvokeAsync([question]);
        Assert.DoesNotContain("Caoimhe", answerBeforeAdding);

        // Act
        await sut.OnNewMessageAsync("test-thread-id", input);

        await sut.OnNewMessageAsync("test-thread-id", question);
        var answerAfterAdding = await sut.OnModelInvokeAsync([question]);

        await sut.ClearStoredMemoriesAsync();
        var answerAfterClearing = await sut.OnModelInvokeAsync([question]);

        // Assert
        Assert.Contains("Caoimhe", answerAfterAdding);
        Assert.DoesNotContain("Caoimhe", answerAfterClearing);
    }

    [Fact(Skip = SkipReason)]
    public async Task CanAddAndRetrieveAgentMemoriesAsync()
    {
        // Arrange
        var question = new ChatMessage(ChatRole.User, "What is your name?");
        var input = new ChatMessage(ChatRole.Assistant, "Hello, I'm a friendly assistant and my name is Caoimhe.");

        var sut = new Mem0Behavior(this._httpClient, new() { AgentId = "test-agent-id" });

        await sut.ClearStoredMemoriesAsync();
        var answerBeforeAdding = await sut.OnModelInvokeAsync([question]);
        Assert.DoesNotContain("Caoimhe", answerBeforeAdding);

        // Act
        await sut.OnNewMessageAsync("test-thread-id", input);

        await sut.OnNewMessageAsync("test-thread-id", question);
        var answerAfterAdding = await sut.OnModelInvokeAsync([question]);

        await sut.ClearStoredMemoriesAsync();
        var answerAfterClearing = await sut.OnModelInvokeAsync([question]);

        // Assert
        Assert.Contains("Caoimhe", answerAfterAdding);
        Assert.DoesNotContain("Caoimhe", answerAfterClearing);
    }

    [Fact(Skip = SkipReason)]
    public async Task DoesNotLeakMessagesAcrossScopesAsync()
    {
        // Arrange
        var question = new ChatMessage(ChatRole.User, "What is your name?");
        var input = new ChatMessage(ChatRole.Assistant, "I'm an AI tutor with a personality. My name is Caoimhe.");

        var sut1 = new Mem0Behavior(this._httpClient, new() { AgentId = "test-agent-id-1" });
        var sut2 = new Mem0Behavior(this._httpClient, new() { AgentId = "test-agent-id-2" });

        await sut1.ClearStoredMemoriesAsync();
        await sut2.ClearStoredMemoriesAsync();

        var answerBeforeAdding1 = await sut1.OnModelInvokeAsync([question]);
        var answerBeforeAdding2 = await sut2.OnModelInvokeAsync([question]);
        Assert.DoesNotContain("Caoimhe", answerBeforeAdding1);
        Assert.DoesNotContain("Caoimhe", answerBeforeAdding2);

        // Act
        await sut1.OnNewMessageAsync("test-thread-id-1", input);
        var answerAfterAdding = await sut1.OnModelInvokeAsync([question]);

        await sut2.OnNewMessageAsync("test-thread-id-2", question);
        var answerAfterAddingOnOtherScope = await sut2.OnModelInvokeAsync([question]);

        // Assert
        Assert.Contains("Caoimhe", answerAfterAdding);
        Assert.DoesNotContain("Caoimhe", answerAfterAddingOnOtherScope);

        // Cleanup.
        await sut1.ClearStoredMemoriesAsync();
        await sut2.ClearStoredMemoriesAsync();
    }

    [Fact(Skip = SkipReason)]
    public async Task DoesNotWorkWithMultiplePerOperationThreadsAsync()
    {
        // Arrange
        var input = new ChatMessage(ChatRole.User, "Hello, my name is Caoimhe.");

        var sut = new Mem0Behavior(this._httpClient, new() { UserId = "test-user-id", ScopeToPerOperationThreadId = true });

        await sut.ClearStoredMemoriesAsync();

        // Act & Assert
        await sut.OnThreadCreatedAsync("test-thread-id-1");
        await Assert.ThrowsAsync<InvalidOperationException>(() => sut.OnThreadCreatedAsync("test-thread-id-2"));

        await sut.OnNewMessageAsync("test-thread-id-1", input);
        await Assert.ThrowsAsync<InvalidOperationException>(() => sut.OnNewMessageAsync("test-thread-id-2", input));

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
