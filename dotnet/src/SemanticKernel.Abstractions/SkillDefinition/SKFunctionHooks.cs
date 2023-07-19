// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.SkillDefinition;

public delegate SKContext PreExecutionHook(SKContext context, string prompt);
public delegate SKContext PostExecutionHook(SKContext context);
