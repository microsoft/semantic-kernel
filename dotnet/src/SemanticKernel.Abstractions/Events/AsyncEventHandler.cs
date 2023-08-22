// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Events;

#pragma warning disable CA1711 // Identifiers should not have incorrect suffix

public delegate Task AsyncEventHandler<TEventArgs>(object? sender, TEventArgs args);
