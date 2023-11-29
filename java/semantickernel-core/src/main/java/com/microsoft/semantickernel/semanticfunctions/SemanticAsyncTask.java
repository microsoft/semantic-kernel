// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

import com.microsoft.semantickernel.orchestration.ContextVariables;
import com.microsoft.semantickernel.orchestration.SKTask;
import com.microsoft.semantickernel.textcompletion.CompletionRequestSettings;
import com.microsoft.semantickernel.textcompletion.TextCompletion;
import java.io.IOException;
import reactor.core.publisher.Mono;

public interface SemanticAsyncTask<Result> extends SKTask<Result> {
    Mono<Result> run(
            TextCompletion client,
            CompletionRequestSettings requestSettings,
            ContextVariables input)
            throws IOException;
}
