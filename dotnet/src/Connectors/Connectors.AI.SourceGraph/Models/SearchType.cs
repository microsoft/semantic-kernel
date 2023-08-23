// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph.Models;

using System.Runtime.Serialization;


public enum SearchType
{

    /// <summary>
    ///  Search for file content matches
    /// </summary>
    [EnumMember(Value = "file")]
    File,

    /// <summary>
    ///  Search for repository name matches
    /// </summary>
    [EnumMember(Value = "repo")]
    Repo,

    /// <summary>
    ///  Search for path matches
    /// </summary>
    [EnumMember(Value = "path")]
    Path,

    /// <summary>
    ///   Search for symbol definitions (functions, classes, etc)
    /// </summary>
    [EnumMember(Value = "symbol")]
    Symbol,

    /// <summary>
    ///  Search for commit messages
    /// </summary>
    [EnumMember(Value = "diff")]
    Diff,

    /// <summary>
    ///  Search for commit messages and diffs
    /// </summary>
    [EnumMember(Value = "commit")]
    Commit

}
