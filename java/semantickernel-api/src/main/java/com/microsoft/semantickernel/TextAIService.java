// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

/**
 * Marker interface for Text AI services, typically Chat or Text generation for OpenAI
 */
public interface TextAIService extends AIService {
    /**
     * The maximum number of results per prompt
     */
    int MAX_RESULTS_PER_PROMPT = 128;

    /**
     * The maximum number of auto-invokes that can be in-flight at any given time as part of the current
     * asynchronous chain of execution.
     * <p>
     * This is a fail-safe mechanism. If someone accidentally manages to set up execution settings in such a way that
     * auto-invocation is invoked recursively, and in particular where a prompt function is able to auto-invoke itself,
     * we could end up in an infinite loop. This const is a backstop against that happening. We should never come close
     * to this limit, but if we do, auto-invoke will be disabled for the current flow in order to prevent runaway execution.
     * With the current setup, the way this could possibly happen is if a prompt function is configured with built-in
     * execution settings that opt-in to auto-invocation of everything in the kernel, in which case the invocation of that
     * prompt function could advertise itself as a candidate for auto-invocation. We don't want to outright block that,
     * if that's something a developer has asked to do (e.g. it might be invoked with different arguments than its parent
     * was invoked with), but we do want to limit it. This limit is arbitrary and can be tweaked in the future and/or made
     * configurable should need arise.
     * </p>
     */
    int MAXIMUM_INFLIGHT_AUTO_INVOKES = 5;
}
