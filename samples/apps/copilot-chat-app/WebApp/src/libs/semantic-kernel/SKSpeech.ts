// Copyright (c) Microsoft. All rights reserved.

import * as speechSdk from 'microsoft-cognitiveservices-speech-sdk';
// import speechkeys from './../../../webapp.development.json';
import fs from 'fs';

//fetchRequestAsync is a function in sk-vnext\apps\InfiniteChat\apps\chatbot-v3\src\libs\semantic-kernel\service\SKService.ts, that i need to map here somehow
// const getAzureSpeechTokenAsync = async () => {
//     const response = await fetchRequestAsync({
//         method: 'GET',
//         apiEndpoint: '/get-azure-speech-token',
//     });

//     return (await response.json()) as { token: string; region: string };
// };

const getSpeechRecognizerAsync = async () => {
    //
    // const response = await getAzureSpeechTokenAsync();
    // const { token, region } = response;
    // const speechConfig = speechSdk.SpeechConfig.fromAuthorizationToken(token, region);

    // resource id: subscriptions/5b742c40-bc2b-4a4f-902f-ee9f644d8844/resourceGroups/lightspeed-team/providers/Microsoft.CognitiveServices/accounts/lightspeed-speech-recognition

    //TODO: figure out a way to not need the key directly

    const config = JSON.parse(fs.readFileSync('./../../../webapp.development.json', 'utf-8')); // Read and Parse the JSON content
    var subscriptionKey = config[0].AzureSpeechSubscriptionKey; //'YourSubscriptionKey';
    var serviceRegion = config[0].AzureSpeechRegion; // e.g., "westus"

    const speechConfig = speechSdk.SpeechConfig.fromSubscription(subscriptionKey, serviceRegion);
    speechConfig.speechRecognitionLanguage = 'en-US';
    const audioConfig = speechSdk.AudioConfig.fromDefaultMicrophoneInput();
    return new speechSdk.SpeechRecognizer(speechConfig, audioConfig);
};

export const SKSpeech = {
    getSpeechRecognizerAsync,
};
