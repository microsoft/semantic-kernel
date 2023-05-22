// Copyright (c) Microsoft. All rights reserved.

import * as speechSdk from 'microsoft-cognitiveservices-speech-sdk';
import { BaseService } from './BaseService';

interface TokenResponse {
    token: string;
    region: string;
    isSuccess: boolean;
}

export class SpeechService extends BaseService {
    validateSpeechKeyAsync = async (accessToken: string) => {
        const response = await this.invokeTokenAsync(accessToken);
        return response;
    };

    getSpeechRecognizerAsyncWithValidKey = async (response: TokenResponse) => {
        const { token, region, isSuccess } = response;

        if(!isSuccess)
        {
            return;
        }

        return this.generateSpeechRecognizer(token, region);
    };

    getSpeechRecognizerAsync = async (accessToken: string) => {
        const response = await this.invokeTokenAsync(accessToken);
        return await this.getSpeechRecognizerAsyncWithValidKey(response);
    };

    private generateSpeechRecognizer ( token: string, region: string) {
        const speechConfig = speechSdk.SpeechConfig.fromAuthorizationToken(token, region);
        speechConfig.speechRecognitionLanguage = 'en-US';
        const audioConfig = speechSdk.AudioConfig.fromDefaultMicrophoneInput();
        return new speechSdk.SpeechRecognizer(speechConfig, audioConfig);
    }

    private invokeTokenAsync = async (accessToken: string): Promise<TokenResponse> => {
        const result = await this.getResponseAsync<TokenResponse>(
            {
                commandPath: `speechToken`,
                method: 'GET',
            },
            accessToken,
        );

        return result;
    };
}