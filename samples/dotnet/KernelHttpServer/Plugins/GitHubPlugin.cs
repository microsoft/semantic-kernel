// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.IO;
using System.IO.Compression;
using System.Net.Http;
using System.Runtime.InteropServices;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Text;

namespace KernelHttpServer.Plugins;

/// <summary>
/// Plugin for interacting with a GitHub repository.
/// </summary>
public class GitHubPlugin
{
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
    private readonly ILogger _logger;
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
    /// Initializes a new instance of the <see cref="GitHubPlugin"/> class.
    /// </summary>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="logger">Optional logger</param>
    public GitHubPlugin(IKernel kernel, ILoggerFactory? loggerFactory = null)
    {
        this._kernel = kernel;
        this._logger = loggerFactory is not null ? loggerFactory.CreateLogger<GitHubPlugin>() : NullLogger.Instance;

        this._summarizeCodeFunction = kernel.CreateSemanticFunction(
            SummarizeCodeSnippetDefinition,
            skillName: nameof(GitHubPlugin),
            description: "Given a snippet of code, summarize the part of the file.",
            maxTokens: MaxTokens,
            temperature: 0.1,
            topP: 0.5);
    }

    /// <summary>
    /// Summarize the code downloaded from the specified URI.
    /// </summary>
    /// <param name="input">URI to download the repository content to be summarized</param>
    /// <param name="repositoryBranch">Name of the repository repositoryBranch which will be downloaded and summarized</param>
    /// <param name="searchPattern">The search string to match against the names of files in the repository</param>
    /// <param name="patToken">Personal access token for private repositories</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Name of the memory collection used to store the code summaries.</returns>
    [SKFunction, SKName("SummarizeRepository"), Description("Downloads a repository and summarizes the content")]
    public async Task<string?> SummarizeRepositoryAsync(
        [Description("URL of the GitHub repository to summarize")] string input,
        [Description("Name of the repository repositoryBranch which will be downloaded and summarized"), DefaultValue("main")] string repositoryBranch,
        [Description("The search string to match against the names of files in the repository"), DefaultValue("*.md")] string searchPattern,
        [Description("Personal access token for private repositories"), Optional] string? patToken,
        CancellationToken cancellationToken = default)
    {
        string tempPath = Path.GetTempPath();
        string directoryPath = Path.Combine(tempPath, $"SK-{Guid.NewGuid()}");
        string filePath = Path.Combine(tempPath, $"SK-{Guid.NewGuid()}.zip");

        try
        {
            var originalUri = input.Trim(s_trimChars);
            var repositoryUri = Regex.Replace(originalUri, "github.com", "api.github.com/repos", RegexOptions.IgnoreCase);
            var repoBundle = $"{repositoryUri}/zipball/{repositoryBranch}";

            this._logger.LogDebug("Downloading {RepoBundle}", repoBundle);

            var headers = new Dictionary<string, string>();
            headers.Add("X-GitHub-Api-Version", "2022-11-28");
            headers.Add("Accept", "application/vnd.github+json");
            headers.Add("User-Agent", "msft-semantic-kernel-sample");
            if (!string.IsNullOrEmpty(patToken))
            {
                this._logger.LogDebug("Access token detected, adding authorization headers");
                headers.Add("Authorization", $"Bearer {patToken}");
            }

            await this.DownloadToFileAsync(repoBundle, headers, filePath, cancellationToken);

            ZipFile.ExtractToDirectory(filePath, directoryPath);

            await this.SummarizeCodeDirectoryAsync(directoryPath, searchPattern, originalUri, repositoryBranch, cancellationToken);

            return $"{originalUri}-{repositoryBranch}";
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

    private async Task DownloadToFileAsync(string uri, IDictionary<string, string> headers, string filePath, CancellationToken cancellationToken = default)
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

        using Stream contentStream = await response.Content.ReadAsStreamAsync(cancellationToken);
        using FileStream fileStream = File.Create(filePath);
        await contentStream.CopyToAsync(fileStream, 81920, cancellationToken);
        await fileStream.FlushAsync(cancellationToken);
    }

    /// <summary>
    /// Summarize a code file into an embedding
    /// </summary>
    private async Task SummarizeCodeFileAsync(string filePath, string repositoryUri, string repositoryBranch, string fileUri, CancellationToken cancellationToken = default)
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
                        id: $"{fileUri}_{i}",
                        cancellationToken: cancellationToken);
                }
            }
            else
            {
                await this._kernel.Memory.SaveInformationAsync(
                     $"{repositoryUri}-{repositoryBranch}",
                     text: $"{code} File:{repositoryUri}/blob/{repositoryBranch}/{fileUri}",
                     id: fileUri,
                     cancellationToken: cancellationToken);
            }
        }
    }

    /// <summary>
    /// Summarize the code found under a directory into embeddings (one per file)
    /// </summary>
    private async Task SummarizeCodeDirectoryAsync(string directoryPath, string searchPattern, string repositoryUri, string repositoryBranch, CancellationToken cancellationToken = default)
    {
        string[] filePaths = Directory.GetFiles(directoryPath, searchPattern, SearchOption.AllDirectories);

        this._logger.LogDebug("Found {0} files to summarize", filePaths.Length);

        if (filePaths != null && filePaths.Length > 0)
        {
            foreach (string filePath in filePaths)
            {
                var fileUri = this.BuildFileUri(directoryPath, filePath, repositoryUri, repositoryBranch);
                await this.SummarizeCodeFileAsync(filePath, repositoryUri, repositoryBranch, fileUri, cancellationToken);
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
