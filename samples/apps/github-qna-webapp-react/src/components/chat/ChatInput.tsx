// Copyright (c) Microsoft. All rights reserved.

import { Button, Input } from '@fluentui/react-components';
import React, { FC, useCallback } from 'react';

import { Send24Regular } from '@fluentui/react-icons';
import { IChatMessage } from './ChatHistoryItem';

interface ChatInputProps {
    onSubmit: (message: IChatMessage) => void;
}

export const ChatInput: FC<ChatInputProps> = (props) => {
    const { onSubmit } = props;
    const [value, setValue] = React.useState<string>('');
    const [previousValue, setPreviousValue] = React.useState<string>('');

    const handleSubmit = (text: string) => {
        onSubmit({ timestamp: new Date().toISOString(), mine: true, author: '', content: text });
        setPreviousValue(text);
        setValue('');
    };

    const onSendClick = useCallback(
        (_e: any) => {
            if (value && value.length > 0) handleSubmit(value);
        },
        // eslint-disable-next-line react-hooks/exhaustive-deps
        [value],
    );

    return (
        <div style={{ display: 'flex', flexDirection: 'row', gap: 10 }}>
            <Input
                style={{ width: '100%' }}
                placeholder="Type a question you have for the repo"
                value={value}
                multiple
                onChange={(e, d) => setValue(d.value)}
                onKeyDown={(event) => {
                    if (event.key === 'Enter' && !event.shiftKey) {
                        event.preventDefault();
                        handleSubmit(value);
                    } else if (event.key === 'ArrowUp') {
                        event.preventDefault();
                        setValue(previousValue);
                    }
                }}
            />
            <Button icon={<Send24Regular />} appearance="subtle" onClick={onSendClick} />
        </div>
    );
};
