// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { SKSpeechService } from './SKSpeech';

export const useSKSpeechService = () => {
    const [skSpeechService] = React.useState(new SKSpeechService());
    return skSpeechService;
};