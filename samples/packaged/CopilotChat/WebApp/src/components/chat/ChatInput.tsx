// Copyright (c) Microsoft. All rights reserved.

import { Button, makeStyles, shorthands, Textarea, tokens } from '@fluentui/react-components';
import { SendRegular } from '@fluentui/react-icons';
import debug from 'debug';
import React from 'react';
import { Constants } from '../../Constants';
import { AlertType } from '../../libs/models/AlertType';
import { useAppDispatch } from '../../redux/app/hooks';
import { setAlert } from '../../redux/features/app/appSlice';

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
                    <Button icon={<SendRegular />} onClick={() => handleSubmit(value)} />
                </div>
            </div>
        </div>
    );
};
