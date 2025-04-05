// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Data;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Data;

/// <summary>
/// Base class for <see cref="ITextSearch"/> integration tests.
/// </summary>
public abstract class BaseTextSearchTests : BaseIntegrationTest
{
    [Fact(Skip = "For manual verification only.")]
    public virtual async Task CanSearchAsync()
    {
        // Arrange
        var textSearch = await this.CreateTextSearchAsync();
        if (textSearch is null)
        {
            return;
        }
        var query = this.GetQuery();

        // Act
        KernelSearchResults<string> stringResults = await textSearch.SearchAsync(query, new() { Top = 4 });

        // Assert
        Assert.NotNull(stringResults);
        var results = await stringResults.Results.ToArrayAsync<string>();
        Assert.Equal(4, results.Length);
        foreach (var result in results)
        {
            Assert.NotEmpty(result);
        }
    }

    [Fact(Skip = "For manual verification only.")]
    public virtual async Task CanGetTextSearchResultsAsync()
    {
        // Arrange
        var textSearch = await this.CreateTextSearchAsync();
        if (textSearch is null)
        {
            return;
        }
        var query = this.GetQuery();

        // Act
        KernelSearchResults<TextSearchResult> textResults = await textSearch.GetTextSearchResultsAsync(query, new() { Top = 4 });

        // Assert
        Assert.NotNull(textResults);
        var results = await textResults.Results.ToArrayAsync<TextSearchResult>();
        Assert.Equal(4, results.Length);
        foreach (var result in results)
        {
            Assert.NotNull(result.Name);
            Assert.NotNull(result.Link);
            Assert.NotNull(result.Value);

            Assert.NotEmpty(result.Name);
            Assert.NotEmpty(result.Link);
            Assert.NotEmpty(result.Value);
        }
    }

    [Fact(Skip = "For manual verification only.")]
    public virtual async Task CanGetSearchResultsAsync()
    {
        // Arrange
        var textSearch = await this.CreateTextSearchAsync();
        if (textSearch is null)
        {
            return;
        }
        var query = this.GetQuery();

        // Act
        KernelSearchResults<object> fullResults = await textSearch.GetSearchResultsAsync(query, new() { Top = 4 });

        // Assert
        Assert.NotNull(fullResults);
        var results = await fullResults.Results.ToArrayAsync<object>();
        Assert.True(this.VerifySearchResults(results, query));
    }

    [Fact(Skip = "For manual verification only.")]
    public virtual async Task UsingTextSearchWithAFilterAsync()
    {
        // Arrange
        var textSearch = await this.CreateTextSearchAsync();
        if (textSearch is null)
        {
            return;
        }
        var query = this.GetQuery();
        var filter = this.GetTextSearchFilter();

        // Act
        KernelSearchResults<object> fullResults = await textSearch.GetSearchResultsAsync(query, new() { Top = 4, Filter = filter });

        // Assert
        Assert.NotNull(fullResults);
        var results = await fullResults.Results.ToArrayAsync<object>();
        Assert.True(this.VerifySearchResults(results, query, filter));
    }

    [Fact(Skip = "For manual verification only.")]
    public virtual async Task FunctionCallingUsingCreateWithSearchAsync()
    {
        // Arrange
        var textSearch = await this.CreateTextSearchAsync();
        if (textSearch is null)
        {
            return;
        }
        var filter = new AutoFunctionInvocationFilter();
        var kernel = this.CreateKernelWithOpenAI();
        kernel.AutoFunctionInvocationFilters.Add(filter);

        var searchPlugin = textSearch.CreateWithSearch("SearchPlugin");
        kernel.Plugins.Add(searchPlugin);

        // Act
        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Required(searchPlugin) };
        KernelArguments arguments = new(settings);
        var result = await kernel.InvokePromptAsync(this.GetQuery(), arguments);

        // Assert
        Assert.Single(filter.Functions);
        Assert.Equal("Search", filter.Functions[0]);
        var results = filter.FunctionResults[0].GetValue<List<string>>();
        Assert.NotNull(results);
        Assert.NotEmpty(results);
    }

    [Fact(Skip = "For manual verification only.")]
    public virtual async Task FunctionCallingUsingCreateWithGetSearchResultsAsync()
    {
        // Arrange
        var textSearch = await this.CreateTextSearchAsync();
        if (textSearch is null)
        {
            return;
        }
        var filter = new AutoFunctionInvocationFilter();
        var kernel = this.CreateKernelWithOpenAI();
        kernel.AutoFunctionInvocationFilters.Add(filter);

        var searchPlugin = textSearch.CreateWithGetSearchResults("SearchPlugin");
        kernel.Plugins.Add(searchPlugin);

        // Act
        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Required(searchPlugin) };
        KernelArguments arguments = new(settings);
        var result = await kernel.InvokePromptAsync(this.GetQuery(), arguments);

        // Assert
        Assert.Single(filter.Functions);
        Assert.Equal("GetSearchResults", filter.Functions[0]);
        var results = filter.FunctionResults[0].GetValue<List<object>>();
        Assert.NotNull(results);
        Assert.NotEmpty(results);
    }

    [Fact(Skip = "For manual verification only.")]
    public virtual async Task FunctionCallingUsingGetTextSearchResultsAsync()
    {
        // Arrange
        var textSearch = await this.CreateTextSearchAsync();
        if (textSearch is null)
        {
            return;
        }
        var filter = new AutoFunctionInvocationFilter();
        var kernel = this.CreateKernelWithOpenAI();
        kernel.AutoFunctionInvocationFilters.Add(filter);

        var searchPlugin = textSearch.CreateWithGetTextSearchResults("SearchPlugin");
        kernel.Plugins.Add(searchPlugin);

        // Act
        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Required(searchPlugin) };
        KernelArguments arguments = new(settings);
        var result = await kernel.InvokePromptAsync(this.GetQuery(), arguments);

        // Assert
        Assert.Single(filter.Functions);
        Assert.Equal("GetTextSearchResults", filter.Functions[0]);
        var results = filter.FunctionResults[0].GetValue<List<TextSearchResult>>();
        Assert.NotNull(results);
        Assert.NotEmpty(results);
    }

    /// <summary>
    /// Create an instance of <see cref="ITextSearch"/>.
    /// </summary>
    public abstract Task<ITextSearch> CreateTextSearchAsync();

    /// <summary>
    /// Create a query to use with the <see cref="ITextSearch"/> instance.
    /// </summary>
    public abstract string GetQuery();

    /// <summary>
    /// Create a <see cref="TextSearchFilter"/> to use with the <see cref="ITextSearch"/> instance.
    /// </summary>
    public abstract TextSearchFilter GetTextSearchFilter();

    /// <summary>
    /// Verify a search result from the instance of <see cref="ITextSearch"/> being used in tests.
    /// </summary>
    public abstract bool VerifySearchResults(object[] results, string query, TextSearchFilter? filter = null);

    /// <summary>
    /// Gets the <see cref="IConfigurationRoot"/> for the test.
    /// </summary>
    protected IConfigurationRoot Configuration { get; } = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<BaseTextSearchTests>()
        .Build();

    #region private
    private Kernel CreateKernelWithOpenAI()
    {
        var configuration = this.Configuration.GetSection("OpenAI").Get<OpenAIConfiguration>();
        Assert.NotNull(configuration);
        Assert.NotNull(configuration.ChatModelId);
        Assert.NotNull(configuration.ApiKey);
        Assert.NotNull(configuration.ServiceId);

        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddOpenAIChatCompletion(
                modelId: configuration.ChatModelId,
                apiKey: configuration.ApiKey);
        Kernel kernel = kernelBuilder.Build();
        return kernel;
    }

    /// <summary>
    /// Implementation of <see cref="IAutoFunctionInvocationFilter"/> that logs the function invocation.
    /// </summary>
    private sealed class AutoFunctionInvocationFilter() : IAutoFunctionInvocationFilter
    {
        public List<string> Functions { get; } = [];
        public List<FunctionResult> FunctionResults { get; } = [];

        /// <inheritdoc />
        public async Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
        {
            this.Functions.Add(context.Function.Name);
            await next(context);
            this.FunctionResults.Add(context.Result);
        }
    }

    #endregion
}
