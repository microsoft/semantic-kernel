// Copyright (c) Microsoft. All rights reserved.

using System;
using Json.Schema.Generation;
using Json.Schema.Generation.Intents;
using DescriptionAttribute = System.ComponentModel.DescriptionAttribute;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Handles the `System.ComponentModel.DescriptionAttribute` for schema generation.
/// </summary>
internal sealed class DescriptionAttributeHandler : IAttributeHandler<DescriptionAttribute>
{
    /// <inheritdoc/>
    public void AddConstraints(SchemaGenerationContextBase context, Attribute attribute)
    {
        if (attribute is DescriptionAttribute descriptionAttribute)
        {
            context.Intents.Add(new DescriptionIntent(descriptionAttribute.Description));
        }
    }
}
