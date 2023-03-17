// Copyright (c) Microsoft. All rights reserved.

import { CSSProperties, FC } from 'react';

interface IData {
    message: IChatMessage;
}

export interface IChatMessage {
    content: string;
    author: string;
    timestamp: string;
    mine: boolean;
}

export const ChatHistoryItem: FC<IData> = ({ message }) => {
    if (!message) {
        throw new Error('Invalid memory');
    }

    const style: CSSProperties = {
        alignSelf: message.mine ? 'flex-end' : 'flex-start',
        backgroundColor: message.mine ? '#E8EBFA' : '#f4f4f4',
        borderRadius: 10,
        padding: '6px 12px',
        maxWidth: '75%',
    };

    const content = message.content.trim().replace(/\n/g, '<br />');

    const time = new Date(message.timestamp).toLocaleTimeString();

    return (
        <div style={style}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                <div style={{ paddingBottom: 10 }}>
                    {message.mine ? null : (
                        <span style={{ paddingRight: 30, fontWeight: 'bold', fontSize: 16 }}>{message.author}</span>
                    )}
                    <span style={{ fontSize: 12 }}> {time}</span>
                </div>
            </div>
            <div dangerouslySetInnerHTML={{ __html: content }} />
        </div>
    );
};
