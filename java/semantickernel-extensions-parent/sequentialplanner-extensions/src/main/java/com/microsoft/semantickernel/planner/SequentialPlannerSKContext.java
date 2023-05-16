// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.planner;

import com.microsoft.semantickernel.orchestration.SKContext;
import reactor.core.publisher.Mono;

import javax.annotation.Nullable;

public interface SequentialPlannerSKContext extends SKContext<SequentialPlannerSKContext> {

    public static final String PlannerMemoryCollectionName = "Planning.SKFunctionsManual";

    public static final String PlanSKFunctionsAreRemembered = "Planning.SKFunctionsAreRemembered";

    public Mono<String> getFunctionsManualAsync(
            @Nullable String semanticQuery, @Nullable SequentialPlannerRequestSettings config);
}
