// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

internal delegate Task<FunctionResult> NativeFunctionDelegate(
    ITextCompletion? textCompletion,
    AIRequestSettings? requestSettings,
    SKContext context,
    CancellationToken cancellationToken);
