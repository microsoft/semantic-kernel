// Copyright (c) Microsoft. All rights reserved.

namespace ProcessWithCloudEvents.Processes.Models;

/// <summary>
/// Object used to store generated document data
/// Since this object is used as parameter and state type by multiple steps,
/// Its members must be public and serializable
/// </summary>
//[DataContract]
public class DocumentInfo
{
    /// <summary>
    /// Id of the document
    /// </summary>
    public string Id { get; set; } = string.Empty;
    /// <summary>
    /// Title of the document
    /// </summary>
    public string Title { get; set; } = string.Empty;
    /// <summary>
    /// Content of the document
    /// </summary>
    public string Content { get; set; } = string.Empty;
}
