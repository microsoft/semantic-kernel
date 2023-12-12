// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.builders.BuildersSingleton;
import com.microsoft.semantickernel.builders.SemanticKernelBuilder;
import com.microsoft.semantickernel.orchestration.ContextVariables;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.skilldefinition.ParameterView;
import com.microsoft.semantickernel.templateengine.PromptTemplateEngine;
import java.util.List;
import reactor.core.publisher.Mono;

/** Interface for prompt template */
public interface PromptTemplate extends Buildable {
}
