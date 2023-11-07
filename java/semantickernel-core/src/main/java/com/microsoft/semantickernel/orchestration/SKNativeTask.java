// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import reactor.core.publisher.Mono;

public interface SKNativeTask<Result> extends SKTask<Result> {
    Mono<Result> run(Result context);
}
