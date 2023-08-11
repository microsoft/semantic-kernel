// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.SkillDefinition;

public delegate Task ExecutionHandler<TExecutionContext>(TExecutionContext context);
