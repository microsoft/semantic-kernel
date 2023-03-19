// Copyright (c) Microsoft. All rights reserved.

export interface IBackendConfig {
    /**
     * An identifier used to map semantic functions to backend,
     * decoupling prompts configurations from the actual model used.
     */
    readonly label: string;
}
