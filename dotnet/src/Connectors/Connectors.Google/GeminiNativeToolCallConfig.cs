// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Connectors.Google.Core;
using Microsoft.SemanticKernel.Connectors.Google.Core.Gemini;

namespace Microsoft.SemanticKernel.Connectors.Google;

/// <summary>
/// Represents the configuration for a Gemini native tool call, specifically for file search operations.
/// </summary>
/// <remarks>This class is used to configure the parameters for invoking a Gemini native tool that performs file
/// searches. It includes settings for specifying file references to be searched. Additional tool configuration can be
/// added here. NOTE: you will need to update both <see cref="GeminiTool"/> and AddNativeTools in <see cref="GeminiRequest"/>
/// as well as add validation to <see cref="GeminiNativeToolExtensions"/></remarks>
public class GeminiNativeToolCallConfig
{
    /// <summary>
    /// Gets or sets the file search tool configuration for the Gemini application.
    /// </summary>
    [JsonPropertyName("fileSearch")]
    public GeminiFileSearchNativeTool? FileSearch { get; set; } = null;

    /// <summary>
    /// Represents a tool for searching files using the Gemini native interface.
    /// </summary>
    /// <remarks>This class is designed to work with the Gemini system to facilitate file searches by
    /// maintaining a list of file references.
    /// As the Google Connector as this moment doesn't support file uplaod or file search import
    /// Operation, you will need to use a seperate library to upload or import files to FileSearch
    /// </remarks>
    /// <param name="fileReferences"></param>
    public sealed class GeminiFileSearchNativeTool(IList<string> fileReferences)
    {
        /// <summary>
        /// Gets or sets the list of file reference names used for searching.
        /// </summary>
        /// <remarks>The file reference is formated as "fileSearchStores/filenane" this should be retrieved from
        /// response of the filesearch import operation. As the Google Connector as this moment doesn't support this
        /// Operation, you will need to use a seperate library to upload or import files to FileSearch</remarks>
        [JsonPropertyName("fileSearchStoreNames")]
        public IList<string> FileReferences { get; set; } = fileReferences;
    }
}
