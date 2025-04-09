// Copyright (c) Microsoft. All rights reserved.

namespace Memory.VectorStoreEmbeddingGeneration;

/// <summary>
/// An attribute that can be used for an embedding property to indicate that it should
/// be generated from one or more text properties located on the same class.
/// </summary>
/// <remarks>
/// This class is part of the <see cref="VectorStore_EmbeddingGeneration"/> sample.
/// </remarks>
[AttributeUsage(AttributeTargets.Property, AllowMultiple = false, Inherited = true)]
public sealed class GenerateTextEmbeddingAttribute : Attribute
{
    /// <summary>
    /// Initializes a new instance of the <see cref="GenerateTextEmbeddingAttribute"/> class.
    /// </summary>
    /// <param name="sourcePropertyName">The name of the property that the embedding should be generated from.</param>
#pragma warning disable CA1019 // Define accessors for attribute arguments
    public GenerateTextEmbeddingAttribute(string sourcePropertyName)
#pragma warning restore CA1019 // Define accessors for attribute arguments
    {
        this.SourcePropertyNames = [sourcePropertyName];
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="GenerateTextEmbeddingAttribute"/> class.
    /// </summary>
    /// <param name="sourcePropertyNames">The names of the properties that the embedding should be generated from.</param>
    public GenerateTextEmbeddingAttribute(string[] sourcePropertyNames)
    {
        this.SourcePropertyNames = sourcePropertyNames;
    }

    /// <summary>
    /// Gets the name of the property to use as the source for generating the embedding.
    /// </summary>
    public string[] SourcePropertyNames { get; }
}
