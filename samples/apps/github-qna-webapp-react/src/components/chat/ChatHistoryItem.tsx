// Copyright (c) Microsoft. All rights reserved.

import { Avatar, Spinner } from '@fluentui/react-components';
import { ErrorCircle20Regular } from '@fluentui/react-icons';
import { CSSProperties, FC } from 'react';
import GithubAvatar from '../../assets/icons8-github-512.png';

interface IData {
    message: IChatMessage;
}

export enum FetchState {
    Fetching = 0,
    Fetched = 1,
    Error = 2,
}

export interface IChatMessage {
    content: string;
    author: string;
    timestamp: string;
    mine: boolean;
    index?: number;
    fetchState?: FetchState;
}

export const ChatHistoryItem: FC<IData> = ({ message }) => {
    if (!message) {
        throw new Error('Invalid memory');
    }

    const style: CSSProperties = {
        backgroundColor: message.mine ? '#E8EBFA' : '#f4f4f4',
        borderRadius: 10,
        padding: '6px 12px',
    };

    const content = message.content.trim().replace(/\n/g, '<br />');

    const time = new Date(message.timestamp).toLocaleTimeString();

    return (
        <div
            style={{
                display: 'flex',
                flexDirection: 'row',
                gap: 10,
                alignSelf: message.mine ? 'flex-end' : 'flex-start',
                maxWidth: '75%',
            }}
        >
            {message.mine ? null : (
                <Avatar
                    image={{
                        src: GithubAvatar,
                    }}
                    color="neutral"
                    badge={{ status: 'available' }}
                />
            )}
            <div style={style}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                    <div style={{ paddingBottom: 10 }}>
                        {message.mine ? null : (
                            <span style={{ paddingRight: 30, fontWeight: 'bold', fontSize: 16 }}>{message.author}</span>
                        )}
                        <span style={{ fontSize: 12 }}> {time}</span>
                    </div>
                </div>
                {message.fetchState === FetchState.Fetching ? (
                    <Spinner size="tiny" style={{ alignSelf: 'flex-start' }} />
                ) : (
                    <div
                        style={{
                            display: 'flex',
                            flexDirection: 'row',
                            gap: 10,
                        }}
                    >
                        {message.fetchState === FetchState.Error ? <ErrorCircle20Regular color="red" /> : null}
                        <div dangerouslySetInnerHTML={{ __html: content }} />
                    </div>
                )}
            </div>
        </div>
    );
};
