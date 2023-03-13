// Copyright (c) Microsoft. All rights reserved.

import React, { FC } from 'react';
import { Input } from "@fluentui/react-components";
import { IChatMessage } from './ChatHistoryItem';

interface ChatInputProps {
    onSubmit: (message: IChatMessage) => void;
}

export const ChatInput: FC<ChatInputProps> = (props) => {
    const { onSubmit } = props;
    const [value, setValue] = React.useState<string>('');
    const [previousValue, setPreviousValue] = React.useState<string>('');

    const handleSubmit = (text: string) => {
        onSubmit({ timestamp: new Date().getTime().toString(), mine: true, author: '', content: text });
        setPreviousValue(text);
        setValue('');
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'row', gap: 10 }}>
            <Input
                style={{ width: '100%' }}
                placeholder="Type your question here"
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
        </div>
    );
};
