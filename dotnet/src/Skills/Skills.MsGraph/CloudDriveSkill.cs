// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Skills.MsGraph.Diagnostics;

namespace Microsoft.SemanticKernel.Skills.MsGraph;

/// <summary>
/// Cloud drive skill (e.g. OneDrive).
/// </summary>
public sealed class CloudDriveSkill
{
    /// <summary>
    /// <see cref="ContextVariables"/> parameter names.
    /// </summary>
    public static class Parameters
    {
        /// <summary>
        /// Document file path.
        /// </summary>
        public const string DestinationPath = "destinationPath";
    }

    private readonly ICloudDriveConnector _connector;
    private readonly ILogger<CloudDriveSkill> _logger;

    public CloudDriveSkill(ICloudDriveConnector connector, ILogger<CloudDriveSkill>? logger = null)
    {
        Ensure.NotNull(connector, nameof(connector));

        this._connector = connector;
        this._logger = logger ?? new NullLogger<CloudDriveSkill>();
    }

    /// <summary>
    /// Get the contents of a file stored in a cloud drive.
    /// </summary>
    [SKFunction, Description("Get the contents of a file in a cloud drive.")]
    public async Task<string> GetFileContentAsync(
        [Description("Path to file")] string filePath,
        CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Getting file content for '{0}'", filePath);
        Stream fileContentStream = await this._connector.GetFileContentStreamAsync(filePath, cancellationToken).ConfigureAwait(false);

        using StreamReader sr = new(fileContentStream);
        string content = await sr.ReadToEndAsync().ConfigureAwait(false);
        this._logger.LogDebug("File content: {0}", content);
        return content;
    }

    /// <summary>
    /// Upload a small file to OneDrive (less than 4MB).
    /// </summary>
    [SKFunction, Description("Upload a small file to OneDrive (less than 4MB).")]
    public async Task UploadFileAsync(
        [Description("Path to file")] string filePath,
        [Description("Remote path to store the file")] string destinationPath,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(destinationPath))
        {
            throw new ArgumentException("Variable was null or whitespace", nameof(destinationPath));
        }

        this._logger.LogDebug("Uploading file '{0}'", filePath);

        // TODO Add support for large file uploads (i.e. upload sessions)
        await this._connector.UploadSmallFileAsync(filePath, destinationPath, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Create a sharable link to a file stored in a cloud drive.
    /// </summary>
    [SKFunction, Description("Create a sharable link to a file stored in a cloud drive.")]
    public async Task<string> CreateLinkAsync(
        [Description("Path to file")] string filePath,
        CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Creating link for '{0}'", filePath);
        const string Type = "view"; // TODO expose this as an SK variable
        const string Scope = "anonymous"; // TODO expose this as an SK variable

        return await this._connector.CreateShareLinkAsync(filePath, Type, Scope, cancellationToken).ConfigureAwait(false);
    }
}
