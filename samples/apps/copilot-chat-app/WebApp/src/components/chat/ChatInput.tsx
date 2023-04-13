// Copyright (c) Microsoft. All rights reserved.

import { Button, makeStyles, shorthands, Textarea, tokens } from '@fluentui/react-components';
import { SendRegular } from '@fluentui/react-icons';
import debug from 'debug';
import React from 'react';
import { Constants } from '../../Constants';
import { AlertType } from '../../libs/models/AlertType';
import { useAppDispatch } from '../../redux/app/hooks';
import { addAlert } from '../../redux/features/app/appSlice';
import { TypingIndicatorRenderer } from './typing-indicator/TypingIndicatorRenderer';

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

    const handleSubmit = (data: string) => {
        try {
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
                    <Button icon={<SendRegular />} onClick={() => handleSubmit(value)} />
                </div>
            </div>
        </div>
    );
};
