// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.Process.TestsShared.Services;

internal interface ICounterService
{
    int IncreateCount();

    int GetCount();
}
