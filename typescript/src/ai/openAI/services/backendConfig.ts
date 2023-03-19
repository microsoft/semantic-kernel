// Copyright (c) Microsoft. All rights reserved.

import { IBackendConfig } from '../../../configuration/iBackendConfig';
import { Verify } from '../../../utils/verify';

export abstract class BackendConfig implements IBackendConfig {
    /**
     * An identifier used to map semantic functions to backend,
     * decoupling prompts configurations from the actual model used.
     */
    public readonly label: string;

    /**
     * Creates a new BackendConfig with supplied values.
     * @param label An identifier used to map semantic functions to backend.
     */
    protected constructor(label: string) {
        Verify.notEmpty(label, 'The configuration label is empty');
        this.label = label;
    }
}
