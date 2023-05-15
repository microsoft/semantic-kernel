// Copyright (c) Microsoft. All rights reserved.

// Licensed to the .NET Foundation under one or more agreements.
// The .NET Foundation licenses this file to you under the MIT license.
// See the LICENSE file in the project root for more information.

#pragma warning disable IDE0130 // Namespace does not match folder structure
// ReSharper disable once CheckNamespace
namespace System.Runtime.CompilerServices;
#pragma warning restore IDE0130

#if !NETCOREAPP

[AttributeUsage(AttributeTargets.Parameter, AllowMultiple = false, Inherited = false)]
internal sealed class CallerArgumentExpressionAttribute : Attribute
{
    public CallerArgumentExpressionAttribute(string parameterName)
    {
        this.ParameterName = parameterName;
    }

    public string ParameterName { get; }
}

#endif
