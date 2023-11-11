// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.AI.ChatCompletion;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

/// <summary>
/// $$$
/// </summary>
public class ChatMessage
{
    /// <summary>
    /// $$$
    /// </summary>
    public string Role { get; set; }

    /// <summary>
    /// $$$
    /// </summary>
    public object Content { get; set; }

    /// <summary>
    /// $$$
    /// </summary>
    public Dictionary<string, object>? Properties { get; set; }

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="content"></param>
    /// <param name="role"></param>
    /// <param name="properties"></param>
    public ChatMessage(object content, string? role = null, Dictionary<string, object>? properties = null)
    {
        this.Role = role ?? AuthorRole.User.Label;
        this.Content = content;
        this.Properties = properties;
    }

    //public override string ToString() $$$ ???
    //{
    //    if (this.Content is IEnumerable enumerable)
    //    {
    //        var sb = new StringBuilder();
    //        foreach (var item in enumerable)
    //        {
    //            sb.Append(item);
    //        }
    //        return sb.ToString();
    //    }

    //    return this.Content.ToString() ?? string.Empty;
    //}
}
