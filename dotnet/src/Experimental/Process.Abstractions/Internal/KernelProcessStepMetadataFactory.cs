// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Reflection;

namespace Microsoft.SemanticKernel.Process.Internal;
/// <summary>
/// Factory that help extract <see cref="KernelProcessStepMetadataAttribute"/>
/// </summary>
public static class KernelProcessStepMetadataFactory
{
    /// <summary>
    /// Extracts <see cref="KernelProcessStepMetadataAttribute"/> from annotations on a <see cref="KernelProcessStep"/> based class.
    /// </summary>
    /// <param name="stepType">specific step type</param>
    /// <returns><see cref="KernelProcessStepMetadataAttribute"/></returns>
    public static KernelProcessStepMetadataAttribute ExtractProcessStepMetadataFromType(Type stepType)
    {
        var attributes = stepType.GetCustomAttributes<KernelProcessStepMetadataAttribute>();
        return attributes?.FirstOrDefault() ?? new KernelProcessStepMetadataAttribute();
    }
}
