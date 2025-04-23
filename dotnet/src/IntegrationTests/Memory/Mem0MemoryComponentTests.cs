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
/// Contains tests for the <see cref="Mem0MemoryComponent"/> class.
/// </summary>
public class Mem0MemoryComponentTests : IDisposable
{
    // If null, all tests will be enabled
    private const string SkipReason = "Requires a Mem0 service configured";

    private readonly Mem0MemoryComponent _sut;
    private readonly HttpClient _httpClient;
    private bool _disposedValue;

    public Mem0MemoryComponentTests()
    {
        IConfigurationRoot configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<Mem0MemoryComponentTests>()
            .Build();

        var mem0Settings = configuration.GetRequiredSection("Mem0").Get<Mem0Configuration>()!;

        this._httpClient = new HttpClient();
        this._httpClient.BaseAddress = new Uri(mem0Settings.ServiceUri);
        this._httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Token", mem0Settings.ApiKey);
        this._sut = new Mem0MemoryComponent(this._httpClient, new() { ThreadId = "test-thread-id", UserId = "test-user-id", ScopeToThread = true });
    }

    [Fact(Skip = SkipReason)]
    public async Task Mem0ComponentCanAddAndRetrieveMemoriesAsync()
    {
        // Arrange
        var question = new ChatMessage(ChatRole.User, "What is my name?");
        var input = new ChatMessage(ChatRole.User, "Hello, my name is Caoimhe.");

        await this._sut.ClearStoredUserFactsAsync();
        var answerBeforeAdding = await this._sut.OnModelInvokeAsync([question]);
        Assert.DoesNotContain("Caoimhe", answerBeforeAdding);

        // Act
        await this._sut.OnNewMessageAsync("test-thread-id", input);

        await this._sut.OnNewMessageAsync("test-thread-id", question);
        var answerAfterAdding = await this._sut.OnModelInvokeAsync([question]);

        await this._sut.ClearStoredUserFactsAsync();
        var answerAfterClearing = await this._sut.OnModelInvokeAsync([question]);

        // Assert
        Assert.Contains("Caoimhe", answerAfterAdding);
        Assert.DoesNotContain("Caoimhe", answerAfterClearing);
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
