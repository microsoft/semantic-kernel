// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.Serialization;
using System.Text.Json;

namespace ProcessWithCloudEvents.Processes.Models;

/// <summary>
/// Object used to store generated document data
/// Since this object is used as parameter and state type by multiple steps,
/// Its members must be public and serializable
/// </summary>
[DataContract]
public class DocumentInfo
{
    /// <summary>
    /// Id of the document
    /// </summary>
    [DataMember]
    public string Id { get; set; } = string.Empty;
    /// <summary>
    /// Title of the document
    /// </summary>
    [DataMember]
    public string Title { get; set; } = string.Empty;
    /// <summary>
    /// Content of the document
    /// </summary>
    [DataMember]
    public string Content { get; set; } = string.Empty;

    /// <summary>
    /// For properly supporting serialization for state management saving and restoring,
    /// objects used in state and parameter types must be serializable.<br/>
    /// Overriding the ToString method allows injecting custom serialization logic if needed.
    /// </summary>
    /// <returns></returns>
    public override string ToString()
    {
        return JsonSerializer.Serialize(this);
    }
}
