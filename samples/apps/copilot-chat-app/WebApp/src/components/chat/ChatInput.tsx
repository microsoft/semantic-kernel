// Copyright (c) Microsoft. All rights reserved.

import { Button, makeStyles, shorthands, Textarea, tokens } from '@fluentui/react-components';
import { MicRegular, SendRegular } from '@fluentui/react-icons';
import debug from 'debug';
import * as speechSdk from 'microsoft-cognitiveservices-speech-sdk';
import React from 'react';
import { Constants } from '../../Constants';
import { AlertType } from '../../libs/models/AlertType';
import { useAppDispatch } from '../../redux/app/hooks';
import { setAlert } from '../../redux/features/app/appSlice';
import { useSKSpeechService } from './../../libs/semantic-kernel/useSKSpeech';

const log = debug(Constants.debug.root).extend('chat-input');

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'center',
        position: 'relative',
    },
    claim: {
        position: 'absolute',
        top: '-150px',
        width: '100%',
    },
    claimContent: {
        ...shorthands.margin(0, 'auto'),
        backgroundColor: tokens.colorNeutralBackground4,
        ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM),
        ...shorthands.borderRadius(tokens.borderRadiusMedium, tokens.borderRadiusMedium, 0, 0),
    },
    content: {
        ...shorthands.gap(tokens.spacingHorizontalM),
        display: 'flex',
        flexDirection: 'row',
        maxWidth: '900px',
        width: '100%',
    },
    input: {
        width: '100%',
    },
    textarea: {
        height: '70px',
    },
    controls: {
        display: 'flex',
        flexDirection: 'column',
        ...shorthands.gap(tokens.spacingVerticalS),
    },
});

interface ChatInputProps {
    onSubmit: (value: string) => void;
}

export const ChatInput: React.FC<ChatInputProps> = (props) => {
    const { onSubmit } = props;
    const classes = useClasses();
    const dispatch = useAppDispatch();
    const [value, setValue] = React.useState('');
    const [previousValue, setPreviousValue] = React.useState('');
    const [recognizer, setRecognizer] = React.useState<speechSdk.SpeechRecognizer>();
    const [isListening, setIsListening] = React.useState(false);
    const speechService = useSKSpeechService();

    React.useEffect(() => {
        if (recognizer) return;
        void (async () => {
            const newRecognizer = await speechService.getSpeechRecognizerAsync();;
            setRecognizer(newRecognizer);
        })();
    }, [recognizer, speechService]);

    const handleSpeech = () => {
        setIsListening(true);

        recognizer?.recognizeOnceAsync((result) => {
            if (result.reason === speechSdk.ResultReason.RecognizedSpeech) {
                if (result.text && result.text.length > 0) {
                    handleSubmit(result.text);
                }
            }
            setIsListening(false);
        });
    };

    const handleSubmit = (data: string) => {
        try {
            onSubmit(data);
            setPreviousValue(data);
            setValue('');
        } catch (error) {
            const message = `Error submitting chat input: ${(error as Error).message}`;
            log(message);
            dispatch(
                setAlert({
                    type: AlertType.Error,
                    message,
                }),
            );
        }
        // void chat.sendTypingStopSignalAsync();
    };

    return (
        <div className={classes.root}>
            <div className={classes.content}>
                <Textarea
                    id="chat-input"
                    resize="vertical"
                    textarea={{ className: classes.textarea }}
                    className={classes.input}
                    value={value}
                    onFocus={() => {
                        // update the locally stored value to the current value
                        const chatInput = document.getElementById('chat-input') as HTMLTextAreaElement;
                        if (chatInput) {
                            setValue(chatInput.value);
                        }
                    }}
                    onChange={(_event, data) => setValue(data.value)}
                    onKeyDown={(event) => {
                        if (event.key === 'Enter' && !event.shiftKey) {
                            event.preventDefault();
                            handleSubmit(value);
                            return;
                        } else if (value === '' && previousValue !== '' && event.key === 'ArrowUp') {
                            event.preventDefault();
                            setValue(previousValue);
                            return;
                        }

                        // void chat.sendTypingStartSignalAsync();
                    }}
                />
                <div className={classes.controls}>
                    {recognizer && (
                        <Button disabled={isListening} icon={<MicRegular />} onClick={() => handleSpeech()} />
                    )}
                    <Button icon={<SendRegular />} onClick={() => handleSubmit(value)} />
                </div>
            </div>
        </div>
    );
};
