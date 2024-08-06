// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.textcompletion.CompletionRequestSettings;
import com.microsoft.semantickernel.textcompletion.TextCompletion;
import reactor.core.publisher.Mono;

public interface SKSemanticAsyncTask<Result> extends SKTask<Result> {
    Mono<Result> run(
            TextCompletion client, CompletionRequestSettings requestSettings, Result context);
}
