// Copyright (c) Microsoft. All rights reserved.

import { Button, makeStyles, shorthands, Textarea, tokens } from '@fluentui/react-components';
import { MicRegular, SendRegular } from '@fluentui/react-icons';
import debug from 'debug';
import React from 'react';
import * as speechSdk from 'microsoft-cognitiveservices-speech-sdk';
import { Constants } from '../../Constants';
import { AlertType } from '../../libs/models/AlertType';
import { useAppDispatch } from '../../redux/app/hooks';
import { addAlert } from '../../redux/features/app/appSlice';
import { TypingIndicatorRenderer } from './typing-indicator/TypingIndicatorRenderer';
import { useSKSpeechService } from './../../libs/semantic-kernel/useSKSpeech';

const log = debug(Constants.debug.root).extend('chat-input');

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        ...shorthands.margin(0, '72px'),
        alignContent: 'stretch',
    },
    typingIndicator: {
        height: '28px',
    },
    content: {
        ...shorthands.gap(tokens.spacingHorizontalM),
        display: 'flex',
        flexDirection: 'row',
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
    // Hardcode to single user typing. For multi-users, it should be a list of ChatUser who are typing.
    isTyping?: boolean;
    onSubmit: (value: string) => void;
}

export const ChatInput: React.FC<ChatInputProps> = (props) => {
    const { isTyping, onSubmit } = props;
    const classes = useClasses();
    const dispatch = useAppDispatch();
    const [value, setValue] = React.useState('');
    const [previousValue, setPreviousValue] = React.useState('');
    const [recognizer, setRecognizer] = React.useState<speechSdk.SpeechRecognizer>();
    const [isListening, setIsListening] = React.useState(false);
    const speechService = useSKSpeechService(process.env.REACT_APP_BACKEND_URI as string);

    React.useEffect(() => {
        if (recognizer) return;
        void (async () => {
            const newRecognizer = await speechService.getSpeechRecognizerAsync();
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
            if (data.trim() === '') {
                return; // only submit if data is not empty
            }
            onSubmit(data);
            setPreviousValue(data);
            setValue('');
        } catch (error) {
            const message = `Error submitting chat input: ${(error as Error).message}`;
            log(message);
            dispatch(
                addAlert({
                    type: AlertType.Error,
                    message,
                }),
            );
        }
        // void chat.sendTypingStopSignalAsync();
    };

    return (
        <div className={classes.root}>
            <div className={classes.typingIndicator}>{isTyping ? <TypingIndicatorRenderer /> : null}</div>
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
