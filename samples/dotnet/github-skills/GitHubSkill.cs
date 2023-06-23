// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Net.Http;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Text;

namespace GitHubSkills;

/// <summary>
/// Skill for interacting with a GitHub repository.
/// </summary>
public class GitHubSkill
{
    /// <summary>
    /// Name of the repository repositoryBranch which will be downloaded and summarized.
    /// </summary>
    public const string RepositoryBranchParamName = "repositoryBranch";

    /// <summary>
    /// The search string to match against the names of files in the repository.
    /// </summary>
    public const string SearchPatternParamName = "searchPattern";

    /// <summary>
    /// Document file path.
    /// </summary>
    public const string FilePathParamName = "filePath";

    /// <summary>
    /// Personal access token for private repositories.
    /// </summary>
    public const string PatTokenParamName = "patToken";

    /// <summary>
    /// Directory to which to extract compressed file's data.
    /// </summary>
    public const string DestinationDirectoryPathParamName = "destinationDirectoryPath";

    /// <summary>
    /// Name of the memory collection used to store the code summaries.
    /// </summary>
    public const string MemoryCollectionNameParamName = "memoryCollectionName";

    /// <summary>
    /// The max tokens to process in a single semantic function call.
    /// </summary>
    private const int MaxTokens = 1024;

    /// <summary>
    /// The max file size to send directly to memory.
    /// </summary>
    private const int MaxFileSize = 2048;

    private readonly ISKFunction _summarizeCodeFunction;
    private readonly IKernel _kernel;
    private readonly ILogger<GitHubSkill> _logger;
    private static readonly char[] s_trimChars = new char[] { ' ', '/' };

    internal const string SummarizeCodeSnippetDefinition =
        @"BEGIN CONTENT TO SUMMARIZE:
{{$INPUT}}
END CONTENT TO SUMMARIZE.

Summarize the content in 'CONTENT TO SUMMARIZE', identifying main points.
Do not incorporate other general knowledge.
Summary is in plain text, in complete sentences, with no markup or tags.

BEGIN SUMMARY:
";

    /// <summary>
    /// Initializes a new instance of the <see cref="GitHubSkill"/> class.
    /// </summary>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="downloadSkill">Instance of WebFileDownloadSkill used to download web files</param>
    /// <param name="logger">Optional logger</param>
    public GitHubSkill(IKernel kernel, ILogger<GitHubSkill>? logger = null)
    {
        this._kernel = kernel;
        this._logger = logger ?? NullLogger<GitHubSkill>.Instance;

        this._summarizeCodeFunction = kernel.CreateSemanticFunction(
            SummarizeCodeSnippetDefinition,
            skillName: nameof(GitHubSkill),
            description: "Given a snippet of code, summarize the part of the file.",
            maxTokens: MaxTokens,
            temperature: 0.1,
            topP: 0.5);
    }

    /// <summary>
    /// Summarize the code downloaded from the specified URI.
    /// </summary>
    /// <param name="source">URI to download the repository content to be summarized</param>
    /// <param name="context">Semantic kernel context</param>
    /// <returns>Task</returns>
    [SKFunction("Downloads a repository and summarizes the content")]
    [SKFunctionName("SummarizeRepository")]
    [SKFunctionInput(Description = "URL of the GitHub repository to summarize")]
    [SKFunctionContextParameter(Name = RepositoryBranchParamName,
        Description = "Name of the repository repositoryBranch which will be downloaded and summarized")]
    [SKFunctionContextParameter(Name = SearchPatternParamName, Description = "The search string to match against the names of files in the repository")]
    public async Task SummarizeRepositoryAsync(string source, SKContext context)
    {
        if (!context.Variables.TryGetValue(RepositoryBranchParamName, out string? repositoryBranch) || string.IsNullOrEmpty(repositoryBranch))
        {
            repositoryBranch = "main";
        }

        if (!context.Variables.TryGetValue(SearchPatternParamName, out string? searchPattern) || string.IsNullOrEmpty(searchPattern))
        {
            searchPattern = "*.md";
        }

        string tempPath = Path.GetTempPath();
        string directoryPath = Path.Combine(tempPath, $"SK-{Guid.NewGuid()}");
        string filePath = Path.Combine(tempPath, $"SK-{Guid.NewGuid()}.zip");

        try
        {
            var repositoryUri = Regex.Replace(source.Trim(s_trimChars), "github.com", "api.github.com/repos", RegexOptions.IgnoreCase);
            var repoBundle = $"{repositoryUri}/zipball/{repositoryBranch}";

            this._logger.LogDebug("Downloading {RepoBundle}", repoBundle);

            var headers = new Dictionary<string, string>();
            if (context.Variables.TryGetValue(PatTokenParamName, out string? pat))
            {
                this._logger.LogDebug("Access token detected, adding authorization headers");
                headers.Add("Authorization", $"Bearer {pat}");
                headers.Add("X-GitHub-Api-Version", "2022-11-28");
                headers.Add("Accept", "application/vnd.github+json");
                headers.Add("User-Agent", "msft-semantic-kernel-sample");
            }

            await this.DownloadToFileAsync(repoBundle, headers, filePath, context.CancellationToken);

            ZipFile.ExtractToDirectory(filePath, directoryPath);

            await this.SummarizeCodeDirectoryAsync(directoryPath, searchPattern, repositoryUri, repositoryBranch, context);

            context.Variables.Set(MemoryCollectionNameParamName, $"{repositoryUri}-{repositoryBranch}");
        }
        finally
        {
            // Cleanup downloaded file and also unzipped content
            if (File.Exists(filePath))
            {
                File.Delete(filePath);
            }

            if (Directory.Exists(directoryPath))
            {
                Directory.Delete(directoryPath, true);
            }
        }
    }

    private async Task DownloadToFileAsync(string uri, IDictionary<string, string> headers, string filePath, CancellationToken cancellationToken)
    {
        // Download URI to file.
        using HttpClient client = new();

        using HttpRequestMessage request = new(HttpMethod.Get, uri);
        foreach (var header in headers)
        {
            client.DefaultRequestHeaders.Add(header.Key, header.Value);
        }

        using HttpResponseMessage response = await client.SendAsync(request, cancellationToken);
        response.EnsureSuccessStatusCode();

        using Stream contentStream = await response.Content.ReadAsStreamAsync();
        using FileStream fileStream = File.Create(filePath);
        await contentStream.CopyToAsync(fileStream, 81920, cancellationToken);
        await fileStream.FlushAsync(cancellationToken);
    }

    /// <summary>
    /// Summarize a code file into an embedding
    /// </summary>
    private async Task SummarizeCodeFileAsync(string filePath, string repositoryUri, string repositoryBranch, string fileUri)
    {
        string code = File.ReadAllText(filePath);

        if (code != null && code.Length > 0)
        {
            if (code.Length > MaxFileSize)
            {
                var extension = new FileInfo(filePath).Extension;

                List<string> lines;
                List<string> paragraphs;

                switch (extension)
                {
                    case ".md":
                    {
                        lines = TextChunker.SplitMarkDownLines(code, MaxTokens);
                        paragraphs = TextChunker.SplitMarkdownParagraphs(lines, MaxTokens);

                        break;
                    }
                    default:
                    {
                        lines = TextChunker.SplitPlainTextLines(code, MaxTokens);
                        paragraphs = TextChunker.SplitPlainTextParagraphs(lines, MaxTokens);

                        break;
                    }
                }

                for (int i = 0; i < paragraphs.Count; i++)
                {
                    await this._kernel.Memory.SaveInformationAsync(
                        $"{repositoryUri}-{repositoryBranch}",
                        text: $"{paragraphs[i]} File:{repositoryUri}/blob/{repositoryBranch}/{fileUri}",
                        id: $"{fileUri}_{i}");
                }
            }
            else
            {
                await this._kernel.Memory.SaveInformationAsync(
                    $"{repositoryUri}-{repositoryBranch}",
                    text: $"{code} File:{repositoryUri}/blob/{repositoryBranch}/{fileUri}",
                    id: fileUri);
            }
        }
    }

    /// <summary>
    /// Summarize the code found under a directory into embeddings (one per file)
    /// </summary>
    private async Task SummarizeCodeDirectoryAsync(string directoryPath, string searchPattern, string repositoryUri, string repositoryBranch, SKContext context)
    {
        string[] filePaths = Directory.GetFiles(directoryPath, searchPattern, SearchOption.AllDirectories);

        if (filePaths != null && filePaths.Length > 0)
        {
            this._logger.LogDebug("Found {0} files to summarize", filePaths.Length);

            foreach (string filePath in filePaths)
            {
                var fileUri = this.BuildFileUri(directoryPath, filePath, repositoryUri, repositoryBranch);
                await this.SummarizeCodeFileAsync(filePath, repositoryUri, repositoryBranch, fileUri);
            }
        }
    }

    /// <summary>
    /// Build the file uri corresponding to the file path.
    /// </summary>
    private string BuildFileUri(string directoryPath, string filePath, string repositoryUri, string repositoryBranch)
    {
        var repositoryBranchName = $"{repositoryUri.Trim('/').Substring(repositoryUri.LastIndexOf('/'))}-{repositoryBranch}";
        return filePath.Substring(directoryPath.Length + repositoryBranchName.Length + 1).Replace('\\', '/');
    }
}
