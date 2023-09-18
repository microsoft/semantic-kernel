// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;
using System.Threading.Tasks;
using System.Threading;

namespace Microsoft.SemanticKernel.SkillDefinition;

internal delegate Task<FunctionResult> NativeFunctionDelegate(
    ITextCompletion? textCompletion,
    CompleteRequestSettings? requestSettings,
    SKContext context,
    CancellationToken cancellationToken);
