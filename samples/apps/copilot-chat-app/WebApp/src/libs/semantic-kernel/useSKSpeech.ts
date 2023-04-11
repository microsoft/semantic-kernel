// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { SKSpeechService } from './SKSpeech';

export const useSKSpeechService = (uri: string) => {
    const [skSpeechService] = React.useState(new SKSpeechService(uri));
    return skSpeechService;
};