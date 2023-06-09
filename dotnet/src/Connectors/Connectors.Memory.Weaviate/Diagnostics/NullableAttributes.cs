// Copyright (c) Microsoft. All rights reserved.

// Licensed to the .NET Foundation under one or more agreements.
// The .NET Foundation licenses this file to you under the MIT license.
// See the LICENSE file in the project root for more information.

// This was copied from https://github.com/dotnet/runtime/blob/39b9607807f29e48cae4652cd74735182b31182e/src/libraries/System.Private.CoreLib/src/System/Diagnostics/CodeAnalysis/NullableAttributes.cs
// and updated to have the scope of the attributes be internal.

#pragma warning disable IDE0130 // Namespace does not match folder structure
// ReSharper disable once CheckNamespace
namespace System.Diagnostics.CodeAnalysis;
#pragma warning restore IDE0130

#if !NETCOREAPP

/// <summary>Specifies that an output will not be null even if the corresponding type allows it.</summary>
[AttributeUsage(AttributeTargets.Field | AttributeTargets.Parameter | AttributeTargets.Property | AttributeTargets.ReturnValue, Inherited = false)]
internal sealed class NotNullAttribute : Attribute
{
}

#endif
