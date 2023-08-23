// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph.Context;

using Client;
using Models;
using Orchestration;
using TemplateEngine;
using static ContextUtils;


internal class CodebaseContext
{
    public CodebaseContext(
        IKernel kernel,
        string codebase,
        ISourceGraphSearchClient searchClient,
        ISourceGraphQLClient contextClient
    )
    {
        _codebase = codebase;
        _searchClient = searchClient;
        _contextClient = contextClient;
    }


    private readonly string _codebase;
    private readonly ISourceGraphSearchClient _searchClient;
    private readonly ISourceGraphQLClient _contextClient;

    public string GetCodebase() => _codebase;


    /// <summary>
    /// Returns list of context messages for a given query, sorted in *reverse* order of importance (that is, * the most important context message appears *last*)
    /// </summary>
    /// <param name="query"></param>
    /// <param name="codeResultCount"></param>
    /// <param name="textResultCount"></param>
    ///  <param name="contextType"></param>
    /// <returns></returns>
    public async IAsyncEnumerable<ContextMessage> GetContextMessagesAsync(string query, int codeResultCount, int textResultCount, ContextType? contextType = ContextType.Embedding)
    {
        IAsyncEnumerable<ContextMessage> contextMessages = contextType switch
        {
            ContextType.Unified => GetUnifiedContextMessagesAsync(query, codeResultCount, textResultCount),
            ContextType.Embedding => GetEmbeddingsContextMessagesAsync(query, codeResultCount, textResultCount),
            _ => throw new ArgumentException($"Invalid context type: {contextType}")
        };

        await foreach (var message in contextMessages)
        {
            yield return message;
        }

    }


    public async IAsyncEnumerable<ContextResult> GetContextSearchResultsAsync(string query, int codeResultCount, int textResultCount, ContextType contextType)
    {
        IEnumerable<ContextResult> results = new List<ContextResult>();

        switch (contextType)
        {
            case ContextType.Unified:
            {
                List<CodeContext>? unifiedContextSearchResults = await GetUnifiedContextSearchResultsAsync(query, codeResultCount, textResultCount).ToListAsync().ConfigureAwait(false);
                results = unifiedContextSearchResults.Select(context => (ContextResult)context);
                break;
            }
            case ContextType.Embedding:
            {
                List<EmbeddingsResult>? embeddingsSearchResults = await GetEmbeddingSearchResultsAsync(query, codeResultCount, textResultCount).ToListAsync().ConfigureAwait(false);
                results = embeddingsSearchResults.Select(result => (ContextResult)result);
                break;
            }
            default:
                throw new ArgumentOutOfRangeException(nameof(contextType), contextType, null);
        }

        foreach (var result in results)
        {
            yield return result;
        }

    }


    private async IAsyncEnumerable<EmbeddingsResult> GetEmbeddingSearchResultsAsync(string query, int codeResultCount, int textResultCount)
    {
        var embeddingsSearchResults = await _searchClient.EmbeddingsSearchAsync(_codebase, query, codeResultCount, textResultCount).ConfigureAwait(false);

        if (embeddingsSearchResults is not { CodeResults: not null, TextResults: not null })
        {
            yield break;
        }
        List<EmbeddingsResult> results = embeddingsSearchResults.CodeResults.Concat(embeddingsSearchResults.TextResults).ToList();

        foreach (var result in results)
        {
            yield return result;
        }

    }


    private async IAsyncEnumerable<ContextMessage> GetEmbeddingsContextMessagesAsync(string query, int codeResultCount, int textResultCount)
    {
        // We split the context into multiple messages instead of joining them into a single giant message.
        // We can gradually eliminate them from the prompt, instead of losing them all at once with a single large message
        // when we run out of tokens.
        List<EmbeddingsResult>? combinedResults = await GetEmbeddingSearchResultsAsync(query, codeResultCount, textResultCount).ToListAsync().ConfigureAwait(false);
        List<FileResult>? resultsGroupedByFile = GroupResultsByFile(combinedResults);
        List<ContextMessage>? allMessages = new();

        foreach (var fileResult in resultsGroupedByFile)
        {
            List<ContextMessage>? messages = await MakeContextMessagesWithResponseAsync(fileResult).ConfigureAwait(false);
            messages.Reverse();
            messages = messages.Select(message => ContextMessageWithSource(message, "embeddings")).ToList();
            allMessages.AddRange(messages);
        }

        foreach (var message in allMessages)
        {
            yield return message;
        }
    }


    private async IAsyncEnumerable<CodeContext> GetUnifiedContextSearchResultsAsync(string query, int codeResultsCount, int textResultsCount)
    {
        List<CodeContext>? response = await _contextClient.GetCodeContextAsync(new[] { _codebase }, query, codeResultsCount, textResultsCount)!.ToListAsync().ConfigureAwait(false);

        foreach (var context in response)
        {
            yield return context;
        }
    }


    private async IAsyncEnumerable<ContextMessage> GetUnifiedContextMessagesAsync(string query, int codeResultCount, int textResultCount)
    {
        List<CodeContext>? results = await GetUnifiedContextSearchResultsAsync(query, codeResultCount, textResultCount).ToListAsync().ConfigureAwait(false);

        foreach (var result in results)
        {
            var content = result.ChunkContent;
            var filePath = result.Blob.Path;
            var repoName = result.Blob.Repository?.Name;
            var revision = result.Blob.Commit?.Oid;

            if (content == null)
            {
                continue;
            }

            var messageText = filePath != null && IsMarkdownFile(filePath)
                ? await PopulateMarkdownContextTemplate(content, filePath, repoName).ConfigureAwait(false)
                : await PopulateCodeContextTemplate(content, filePath!, repoName).ConfigureAwait(false);

            IEnumerable<ContextMessage> contextMessages = GetContextMessageWithResponse(messageText, new FileContext
                { FileName = filePath, RepoName = repoName, Revision = revision });

            foreach (var message in contextMessages)
            {
                yield return message;
            }
        }
    }


    private static async Task<List<ContextMessage>> MakeContextMessagesWithResponseAsync(FileResult groupedResults)
    {
        Func<string, string, string, Task<string>> contextTemplateFn = groupedResults.FileContext.FileName != null && IsMarkdownFile(groupedResults.FileContext.FileName)
            ? PopulateMarkdownContextTemplate
            : PopulateCodeContextTemplate;

        List<ContextMessage> contextMessages = new();

        if (groupedResults.Results == null)
        {
            return contextMessages;
        }

        foreach (var text in groupedResults.Results)
        {
            var template = await contextTemplateFn(text, groupedResults.FileContext.FileName!, groupedResults.FileContext.RepoName!).ConfigureAwait(false);
            IEnumerable<ContextMessage> contextMessage = GetContextMessageWithResponse(template, groupedResults.FileContext);

            contextMessages.AddRange(contextMessage);
        }

        return contextMessages;
    }


    private static Task<string> PopulateCodeContextTemplate(string content, string fileName, string? repoName = null)
    {
        var promptTemplateEngine = new PromptTemplateEngine();
        var template = repoName == null ? CodeContextTemplate : CodeContextTemplateWithRepo;

        SKContext context = new();
        context.Variables.Set("filePath", fileName);
        context.Variables.Set("language", Path.GetExtension(fileName));
        context.Variables.Set("text", content);

        if (repoName != null)
        {
            context.Variables.Set("repoName", repoName);
        }

        return promptTemplateEngine.RenderAsync(template, context);
    }


    private static Task<string> PopulateMarkdownContextTemplate(string content, string fileName, string? repoName)
    {
        var promptTemplateEngine = new PromptTemplateEngine();
        var template = repoName == null ? MarkdownContextTemplate : MarkdownContextTemplateWithRepo;

        SKContext context = new();
        context.Variables.Set("filePath", fileName);
        context.Variables.Set("text", content);

        if (repoName != null)
        {
            context.Variables.Set("repoName", repoName);
        }

        return promptTemplateEngine.RenderAsync(template, context);
    }


    private static ContextMessage ContextMessageWithSource(ContextMessage message, string source)
    {
        if (message.FileContext != null)
        {
            message.FileContext.Source = source;
        }
        return message;
    }


    private static IEnumerable<ContextMessage> GetContextMessageWithResponse(string messageText, FileContext file, string response = "Ok")
    {
        return new[]
        {
            new ContextMessage(SpeakerType.Human, messageText, file),
            new ContextMessage(SpeakerType.Assistant, response)
        };
    }


    private static bool IsMarkdownFile(string fileName) => Path.GetExtension(fileName) == ".md" || Path.GetExtension(fileName) == ".markdown";

    private const string CodeContextTemplate = @"Use following code snippet from file {{$filePath}}:
```{{$language}}}
{{$text}}
```";

    private const string CodeContextTemplateWithRepo = @"Use following code snippet from file {{$filePath}} in repository {{$repoName}}:
```{{$language}}}
{{$text}}
```";

    private const string MarkdownContextTemplate = @"Use the following text from file {{$filePath}}:
{{$text}}";

    private const string MarkdownContextTemplateWithRepo = @"Use the following text from file {{$filePath}} in repository {{$repoName}}:
{{$text}}";

}
