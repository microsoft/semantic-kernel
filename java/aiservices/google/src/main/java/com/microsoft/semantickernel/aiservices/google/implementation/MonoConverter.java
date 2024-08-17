// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.aiservices.google.implementation;

import com.google.api.core.ApiFuture;
import reactor.core.publisher.Mono;

public class MonoConverter {
    public static <T> Mono<T> fromApiFuture(ApiFuture<T> apiFuture) {
        return Mono.create(sink -> {
            apiFuture.addListener(() -> {
                try {
                    T result = apiFuture.get();
                    sink.success(result);
                } catch (Exception e) {
                    sink.error(e);
                }
            }, runnable -> new Thread(runnable).start());
        });
    }
}
