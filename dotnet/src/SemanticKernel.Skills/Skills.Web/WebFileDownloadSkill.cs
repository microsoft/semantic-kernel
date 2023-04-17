// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Skills.Web;

/// <summary>
/// Skill to download web files.
/// </summary>
public class WebFileDownloadSkill : IDisposable
{
    /// <summary>
    /// Parameter names.
    /// <see cref="ContextVariables"/>
    /// </summary>
    public static class Parameters
    {
        /// <summary>
        /// Where to save file.
        /// </summary>
        public const string FilePath = "filePath";
    }

    private readonly ILogger _logger;
    private readonly HttpClientHandler _httpClientHandler;
    private readonly HttpClient _httpClient;

    /// <summary>
    /// Constructor for WebFileDownloadSkill.
    /// </summary>
    /// <param name="logger">Optional logger.</param>
    public WebFileDownloadSkill(ILogger<WebFileDownloadSkill>? logger = null)
    {
        this._logger = logger ?? NullLogger<WebFileDownloadSkill>.Instance;
        this._httpClientHandler = new() { CheckCertificateRevocationList = true };
        this._httpClient = new HttpClient(this._httpClientHandler);
    }

    /// <summary>
    /// Downloads a file to a local file path.
    /// </summary>
    /// <param name="source">URI of file to download</param>
    /// <param name="context">Semantic Kernel context</param>
    /// <returns>Task.</returns>
    /// <exception cref="KeyNotFoundException">Thrown when the location where to download the file is not provided</exception>
    [SKFunction("Downloads a file to local storage")]
    [SKFunctionName("DownloadToFile")]
    [SKFunctionInput(Description = "URL of file to download")]
    [SKFunctionContextParameter(Name = Parameters.FilePath, Description = "Path where to save file locally")]
    public async Task DownloadToFileAsync(string source, SKContext context)
    {
        this._logger.LogDebug($"{nameof(this.DownloadToFileAsync)} got called");

        if (!context.Variables.Get(Parameters.FilePath, out string filePath))
        {
            this._logger.LogError($"Missing context variable in {nameof(this.DownloadToFileAsync)}");
            string errorMessage = $"Missing variable {Parameters.FilePath}";
            context.Fail(errorMessage);

            return;
        }

        this._logger.LogDebug("Sending GET request for {0}", source);
        HttpResponseMessage response = await this._httpClient.GetAsync(new Uri(source), context.CancellationToken);
        response.EnsureSuccessStatusCode();
        this._logger.LogDebug("Response received: {0}", response.StatusCode);

        using Stream webStream = await response.Content.ReadAsStreamAsync();
        using FileStream outputFileStream = new(Environment.ExpandEnvironmentVariables(filePath), FileMode.Create);

        await webStream.CopyToAsync(outputFileStream, (int)webStream.Length, cancellationToken: context.CancellationToken);
    }

    /// <summary>
    /// Implementation of IDisposable.
    /// </summary>
    public void Dispose()
    {
        // Do not change this code. Put cleanup code in 'Dispose(bool disposing)' method
        this.Dispose(disposing: true);
        GC.SuppressFinalize(this);
    }

    /// <summary>
    /// Code that does the actual disposal of resources.
    /// </summary>
    /// <param name="disposing">Dispose of resources only if this is true.</param>
    protected virtual void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._httpClient.Dispose();
            this._httpClientHandler.Dispose();
        }
    }
}
