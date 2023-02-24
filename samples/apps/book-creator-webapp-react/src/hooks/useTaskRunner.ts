// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { IKeyConfig } from '../model/KeyConfig';
import { SemanticKernel } from './SemanticKernel';
import { TaskRunner } from './TaskRunner';

export const useTaskRunner = (sk: SemanticKernel, keyConfig: IKeyConfig, maxSteps: number = 10) => {
    const [taskRunner] = React.useState(new TaskRunner(sk, keyConfig, maxSteps));
    return taskRunner;
};
