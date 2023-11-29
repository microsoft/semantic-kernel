package com.microsoft.semantickernel.v1.semanticfunctions;

import com.microsoft.semantickernel.orchestration.SKTask;
import com.microsoft.semantickernel.textcompletion.CompletionRequestSettings;
import com.microsoft.semantickernel.textcompletion.TextCompletion;
import reactor.core.publisher.Mono;

import java.io.IOException;
import java.util.Map;

public interface SemanticAsyncTask<Result> extends SKTask<Result> {
    Mono<Result> run(
            TextCompletion client, CompletionRequestSettings requestSettings, Map<String, Object> input) throws IOException;
}
