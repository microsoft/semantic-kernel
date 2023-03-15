// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.KernelExtensions;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Skills.Document;
using Microsoft.SemanticKernel.Skills.Web;

namespace Microsoft.SemanticKernel.Skills.Code;

/// <summary>
/// Skill for interacting with code files (e.g. C#)
/// </summary>
public class CodeSkill
{
    /// <summary>
    /// Parameter names.
    /// <see cref="ContextVariables"/>
    /// </summary>
    public static class Parameters
    {
        /// <summary>
        /// Document file path.
        /// </summary>
        public const string FilePath = "filePath";

        /// <summary>
        /// Directory to which to extract compressed file's data.
        /// </summary>
        public const string DestinationDirectoryPath = "destinationDirectoryPath";

        /// <summary>
        /// Name of the memory collection used to store the code summaries.
        /// </summary>
        public const string MemoryCollectionName = "memoryCollectionName";
    }

    /// <summary>
    /// The max tokens to process in a single semantic function call.
    /// </summary>
    private const int MaxTokens = 1024;

    private readonly ISKFunction _summarizeCodeFunction;
    private readonly IKernel _kernel;
    private readonly WebFileDownloadSkill _downloadSkill;
    private readonly DocumentSkill _documentSkill;
    private readonly ILogger<CodeSkill> _logger;

    internal const string SummarizeCodeSnippetDefinition =
    @"BEGIN CONTENT TO SUMMARIZE:
{{$INPUT}}
END CONTENT TO SUMMARIZE.

Summarize the content in 'CONTENT TO SUMMARIZE', identifying main points.
Do not incorporate other general knowledge.
Summary is in plain text, in complete sentences, with no markup or tags.

BEGIN SUMMARY:
";

    internal const string MemoryCollectionName = "CodeSkillMemory"; // TODO Should this be configurable


    /// <summary>
    /// Initializes a new instance of the <see cref="CodeSkill"/> class.
    /// </summary>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="downloadSkill">Instance of WebFileDownloadSkill used to download web files</param>
    /// <param name="documentSkill">Instance of DocumentSkill used to read files</param>
    /// <param name="fileCompressionSkill">Instance of FileCompressionSkill used to unzip files</param>
    /// <param name="logger">Optional logger</param>
    public CodeSkill(IKernel kernel, WebFileDownloadSkill downloadSkill, DocumentSkill documentSkill, ILogger<CodeSkill>? logger = null)
    {
        this._kernel = kernel;
        this._downloadSkill = downloadSkill;
        this._documentSkill = documentSkill;
        this._logger = logger ?? NullLogger<CodeSkill>.Instance;

        this._summarizeCodeFunction = kernel.CreateSemanticFunction(
            SummarizeCodeSnippetDefinition,
            skillName: nameof(CodeSkill),
            description: "Given a snippet of code, summarize the part of the file.",
            maxTokens: MaxTokens,
            temperature: 0.1,
            topP: 0.5);
    }

    /// <summary>
    /// Summarize a code file into an embedding
    /// </summary>
    /// <param name="filePath">Path of file to summarize</param>
    /// <param name="context">Semantic kernal context</param>
    /// <returns>Task</returns>
    public async Task SummarizeCodeFileAsync(string filePath, SKContext context)
    {
        // TODO do we need to extend the DocumentSkill to read raw content?
        // string code = await this._documentSkill.ReadTextAsync(filePath, context);
        string code = File.ReadAllText(filePath);

        if (code != null && code.Length > 0)
        {
            // TODO should I create a new SKContext
            context.Variables.Update(code);
            await this._summarizeCodeFunction.InvokeAsync(context);

            var result = context.Variables.ToString();
            // await this._kernel.Memory.SaveReferenceAsync(MemoryCollectionName, text: result, externalId: filePath, externalSourceName: filePath);
            await this._kernel.Memory.SaveInformationAsync(MemoryCollectionName, text: result, id: filePath);
        }
    }

    /// <summary>
    /// Summarize the code found under a directory into embeddings (one per file)
    /// </summary>
    /// <param name="directoryPath">Path of directory to summarize</param>
    /// <param name="context">Semantic kernal context</param>
    /// <returns>Task</returns>
    public async Task SummarizeCodeDirectoryAsync(string directoryPath, SKContext context)
    {
        // string[] filePaths = await this._documentSkill.RecursivelyListDocumentsUnderDirectoryAsync(directoryPath, context);
        string[] filePaths = await Task.FromResult(Directory.GetFiles(directoryPath, "*.md", SearchOption.AllDirectories));

        if (filePaths != null && filePaths.Length > 0)
        {
            this._logger.LogDebug("Found {0} files to summarize", filePaths.Length);

            foreach (string filePath in filePaths)
            {
                await this.SummarizeCodeFileAsync(filePath, context);
            }

            _ = context.Variables.Update($"Found {filePaths.Length} files to summarize");
            context.Variables.Set(Parameters.MemoryCollectionName, MemoryCollectionName);
        }
    }

    /// <summary>
    /// Summarize the code downloaded from the specified URI.
    /// </summary>
    /// <param name="source">URI to download the respository content to be summarized</param>
    /// <param name="context">Semantic kernal context</param>
    /// <returns>Task</returns>
    [SKFunction("Downloads a repository and summarizes the content")]
    [SKFunctionName("SummarizeRepository")]
    [SKFunctionInput(Description = "URL of repository to summarize")]
    public async Task SummarizeRepositoryAsync(string source, SKContext context)
    {
        string filePath = Environment.ExpandEnvironmentVariables($"%temp%\\SK-{Guid.NewGuid()}.zip");
        string directoryPath = Environment.ExpandEnvironmentVariables($"%temp%\\SK-{Guid.NewGuid()}");

        try
        {
            context.Variables.Set(Parameters.FilePath, filePath);
            await this._downloadSkill.DownloadToFileAsync(source, context);
            context.Variables.Set(Parameters.FilePath, null);

            filePath = Environment.ExpandEnvironmentVariables(filePath);
            ZipFile.ExtractToDirectory(filePath, directoryPath);

            await this.SummarizeCodeDirectoryAsync(directoryPath, context);
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
}
