// Copyright (c) Microsoft. All rights reserved.

import { Body1, Button, Title3 } from '@fluentui/react-components';
import React, { FC, useState } from 'react';
import { ChatHistoryItem } from './ChatHistoryItem';
import { ChatInput } from './ChatInput';
import { ChatThread, IChatMessage } from './ChatThread';

interface IData {
    uri: string;
    onGetAISummary: (chat: IChatMessage[]) => void;
    onBack: () => void;
}

const ChatInteraction: FC<IData> = ({ uri, onGetAISummary, onBack }) => {
    const chatBottomRef = React.useRef<HTMLDivElement>(null);
    const [isBusy, setIsBusy] = useState<boolean>();
    const [chatHistory, setChatHistory] = useState<IChatMessage[]>(ChatThread);

    React.useEffect(() => {
        chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [isBusy]);

    return (
        <div style={{ paddingTop: 20, gap: 20, display: 'flex', flexDirection: 'column', alignItems: 'stretch' }}>
            <Title3 style={{ alignItems: 'left' }}>Interact with Chat</Title3>
            <Body1>
                This is not an interactive chat session. Modify the chat contents by editing ChatThread.ts - you can
                also add to the chat by typing a message below and pressing enter.
            </Body1>

            <div
                style={{
                    position: 'relative',
                    maxHeight: '70vh',
                    display: 'grid',
                    gridTemplateColumns: 'minmax(300px, 800px)',
                    gridTemplateRows: 'auto 1fr auto',
                    gridTemplateAreas: "'menu' 'content' 'footer'",
                    justifyContent: 'center',
                    padding: '0 1rem',
                }}
            >
                <div style={{ gridArea: 'content', overflowY: 'auto', overflowX: 'hidden', padding: '1rem 0' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                        {chatHistory.map((m, idx) => (
                            <ChatHistoryItem key={idx} message={m} />
                        ))}
                        <div ref={chatBottomRef} />
                    </div>
                </div>
                <div style={{ gridArea: 'footer', padding: '1rem 0', borderTop: '1px solid #ccc' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                        <ChatInput
                            onSubmit={(m) => {
                                setIsBusy(true);
                                setChatHistory([...chatHistory, m]);
                                setIsBusy(false);
                            }}
                        />
                        <Body1>Finished chatting? Next, get your AI Summary.</Body1>
                        <div style={{ display: 'flex', flexDirection: 'row', gap: 20 }}>
                            <Button style={{ width: 54 }} appearance="secondary" onClick={() => onBack()}>
                                Back
                            </Button>
                            <Button
                                style={{ width: 175 }}
                                appearance="primary"
                                onClick={() => onGetAISummary(chatHistory)}
                            >
                                Get AI Summary
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ChatInteraction;
