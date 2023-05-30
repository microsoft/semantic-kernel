// Copyright (c) Microsoft. All rights reserved.

using System.IO;
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
public class CloudDriveSkill
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
    [SKFunction("Get the contents of a file in a cloud drive.")]
    [SKFunctionInput(Description = "Path to file")]
    public async Task<string> GetFileContentAsync(string filePath, SKContext context)
    {
        this._logger.LogDebug("Getting file content for '{0}'", filePath);
        Stream fileContentStream = await this._connector.GetFileContentStreamAsync(filePath, context.CancellationToken).ConfigureAwait(false);

        using StreamReader sr = new(fileContentStream);
        string content = await sr.ReadToEndAsync().ConfigureAwait(false);
        this._logger.LogDebug("File content: {0}", content);
        return content;
    }

    /// <summary>
    /// Upload a small file to OneDrive (less than 4MB).
    /// </summary>
    [SKFunction("Upload a small file to OneDrive (less than 4MB).")]
    public async Task UploadFileAsync(string filePath, SKContext context)
    {
        if (!context.Variables.TryGetValue(Parameters.DestinationPath, out string? destinationPath))
        {
            context.Fail($"Missing variable {Parameters.DestinationPath}.");
            return;
        }

        this._logger.LogDebug("Uploading file '{0}'", filePath);

        // TODO Add support for large file uploads (i.e. upload sessions)

        try
        {
            await this._connector.UploadSmallFileAsync(filePath, destinationPath, context.CancellationToken).ConfigureAwait(false);
        }
        catch (IOException ex)
        {
            context.Fail(ex.Message, ex);
        }
    }

    /// <summary>
    /// Create a sharable link to a file stored in a cloud drive.
    /// </summary>
    [SKFunction("Create a sharable link to a file stored in a cloud drive.")]
    [SKFunctionInput(Description = "Path to file")]
    public async Task<string> CreateLinkAsync(string filePath, SKContext context)
    {
        this._logger.LogDebug("Creating link for '{0}'", filePath);
        const string Type = "view"; // TODO expose this as an SK variable
        const string Scope = "anonymous"; // TODO expose this as an SK variable

        return await this._connector.CreateShareLinkAsync(filePath, Type, Scope, context.CancellationToken).ConfigureAwait(false);
    }
}
