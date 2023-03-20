// Copyright (c) Microsoft. All rights reserved.

import { ISKFunction } from '../orchestration/iSKFunction';
import { IReadOnlySkillCollection } from './iReadOnlySkillCollection';

/**
 * Skill collection interface.
 */
export interface ISkillCollection extends IReadOnlySkillCollection {
    // Readonly only access into the collection
    readonly readOnlySkillCollection: IReadOnlySkillCollection;

    /**
     * Add a semantic function to the collection.
     *
     * @param functionInstance Wrapped function delegate.
     * @returns Self instance.
     */
    addSemanticFunction(functionInstance: ISKFunction): ISkillCollection;

    /**
     * Add a native function to the collection.
     *
     * @param functionInstance Wrapped function delegate.
     * @returns Self instance.
     */
    addNativeFunction(functionInstance: ISKFunction): ISkillCollection;
}
