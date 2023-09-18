// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.SkillDefinition;

internal delegate Task<FunctionResult> NativeFunctionDelegate(
    ITextCompletion? textCompletion,
    CompleteRequestSettings? requestSettings,
    SKContext context,
    CancellationToken cancellationToken);
