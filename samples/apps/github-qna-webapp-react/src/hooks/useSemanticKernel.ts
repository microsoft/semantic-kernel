// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { SemanticKernel } from './SemanticKernel';


export const useSemanticKernel = (uri: string) => {
    const [semanticKernel] = React.useState(new SemanticKernel(uri));
    return semanticKernel;
};
