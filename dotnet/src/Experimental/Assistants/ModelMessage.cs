// Copyright (c) Microsoft. All rights reserved.

using System.Collections;
using System.Collections.Generic;
using System.Text;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

public class ModelMessage
{
    public string Role { get; set; }
    public object Content { get; set; }
    public Dictionary<string, object>? Properties { get; set; }

    public ModelMessage(object content, string role = "user", Dictionary<string, object>? properties = default)
    {
        this.Role = role;
        this.Content = content;
        this.Properties = properties;
    }

    public override string ToString()
    {
        if (this.Content is IEnumerable enumerable)
        {
            var sb = new StringBuilder();
            foreach (var item in enumerable)
            {
                sb.Append(item);
            }
            return sb.ToString();
        }
        return this.Content.ToString() ?? string.Empty;
    }
}
