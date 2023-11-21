// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

#pragma warning disable IDE0130

// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;

/// <summary>Provides a collection of <see cref="ISKPlugin"/>s.</summary>
public interface ISKPluginCollection : ICollection<ISKPlugin>, IReadOnlySKPluginCollection
{
}
