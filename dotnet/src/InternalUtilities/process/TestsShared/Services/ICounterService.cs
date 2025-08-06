// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Process.TestsShared.Services;

/// <summary>
/// Interface for Counter Service used by <see cref="TestsShared.Steps.CommonSteps.CountStep"/>
/// </summary>
public interface ICounterService
{
    /// <summary>
    /// Increase count
    /// </summary>
    /// <returns></returns>
    int IncreaseCount();

    /// <summary>
    /// Get current count
    /// </summary>
    /// <returns></returns>
    int GetCount();

    /// <summary>
    /// Set counter to specific value
    /// </summary>
    /// <param name="count"></param>
    /// <returns></returns>
    void SetCount(int count);
}
