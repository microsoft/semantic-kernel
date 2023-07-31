// Copyright (c) Microsoft. All rights reserved.

import { Body1, Button, Caption1, Spinner, Subtitle1, Subtitle2, Title3 } from '@fluentui/react-components';
import { Card, CardHeader } from '@fluentui/react-components/unstable';
import { FC, useEffect, useState } from 'react';
import { useSemanticKernel } from '../hooks/useSemanticKernel';
import { IKeyConfig } from '../model/KeyConfig';
import { IChatMessage } from './chat/ChatThread';

interface IData {
    uri: string;
    chat: IChatMessage[];
    keyConfig: IKeyConfig;
    onBack: () => void;
}

const AISummary: FC<IData> = ({ uri, chat, keyConfig, onBack }) => {
    const sk = useSemanticKernel(uri);
    const [summary, setSummary] = useState<string>();
    const [actionItems, setActionItems] = useState<string>();
    const [topics, setTopics] = useState<string>();

    const getSummary = async (ask: any) => {
        try {
            var result = await sk.invokeAsync(keyConfig, ask, 'ConversationSummarySkill', 'SummarizeLongConversation');
            setSummary(result.value);
        } catch (e) {
            alert('Something went wrong.\n\nDetails:\n' + e);
        }
    };

    const getActionItems = async (ask: any) => {
        try {
            var result = await sk.invokeAsync(keyConfig, ask, 'ConversationSummarySkill', 'GetLongConversationActionItems');
            setActionItems(result.value);
        } catch (e) {
            alert('Something went wrong.\n\nDetails:\n' + e);
        }
    };

    const formatActionItems = (actionItems: string): JSX.Element => {
        var actionItemsJson = JSON.parse(
            '[' +
                actionItems
                    .split('}\n\n{')
                    .map((item, index, array) => {
                        if (array.length === 1) {
                            return item;
                        } else if (index === 0) {
                            return item + '}';
                        } else if (index === array.length - 1) {
                            return '{' + item;
                        } else {
                            return '{' + item + '}';
                        }
                    })
                    .join(',') +
                ']',
        );

        var actionItemsList = actionItemsJson.reduce((acc: any, cur: any) => {
            return acc.concat(cur.actionItems);
        }, []);

        var actionItemsFormatted = actionItemsList.map((actionItem: any) => {
            return (
                <Card>
                    <CardHeader header={<Subtitle2>{actionItem.actionItem}</Subtitle2>} />
                    <Body1>
                        <b>Owner:</b> {actionItem.owner}
                    </Body1>
                    <Body1>
                        <b>Due Date:</b> {actionItem.dueDate}
                    </Body1>
                </Card>
            );
        });

        return (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 20 }}>{actionItemsFormatted}</div>
        );
    };

    const getTopics = async (ask: any) => {
        try {
            var result = await sk.invokeAsync(keyConfig, ask, 'ConversationSummarySkill', 'GetLongConversationTopics');
            setTopics(result.value);
        } catch (e) {
            alert('Something went wrong.\n\nDetails:\n' + e);
        }
    };

    const formatTopics = (topics: string): JSX.Element => {
        var topicsJson = JSON.parse(
            '[' +
                topics
                    .split('}\n\n{')
                    .map((item, index, array) => {
                        if (array.length === 1) {
                            return item;
                        } else if (index === 0) {
                            return item + '}';
                        } else if (index === array.length - 1) {
                            return '{' + item;
                        } else {
                            return '{' + item + '}';
                        }
                    })
                    .join(',') +
                ']',
        );

        var topicsList = topicsJson.reduce((acc: any, cur: any) => {
            return acc.concat(cur.topics);
        }, []);

        var topicsFormatted = topicsList.map((topic: any) => {
            return (
                <Card appearance="outline" size="small">
                    <Caption1>{topic}</Caption1>
                </Card>
            );
        });
        return (
            <div style={{ display: 'flex', flexDirection: 'row', flexWrap: 'wrap', gap: 10 }}>{topicsFormatted}</div>
        );
    };

    useEffect(() => {
        const fetchAsync = async () => {
            var ask = {
                value: chat.map((c) => (c.mine ? `I said: ${c.content}` : `${c.author} said: ${c.content}`)).join('\n'),
            };

            await getSummary(ask);
            await getActionItems(ask);
            await getTopics(ask);
        };
        fetchAsync();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [uri]);

    return (
        <div style={{ padding: 80, gap: 20, display: 'flex', flexDirection: 'column', alignItems: 'left' }}>
            <Title3>AI summaries based on your chat</Title3>
            <Body1>
                We used skills to summarise the conversations from the chat, along with found topics and action items.
            </Body1>
            <br />
            <Subtitle1>
                <strong>Summary</strong>
            </Subtitle1>

            {summary === undefined ? (
                <></>
            ) : (
                <Body1>{summary.length > 0 ? summary : 'We could not create a summary.'}</Body1>
            )}
            {topics === undefined ? (
                <></>
            ) : (
                <Body1>{topics.length > 0 ? formatTopics(topics) : "We didn't find any topics."}</Body1>
            )}
            {summary === undefined || topics === undefined ? <Spinner /> : <div style={{ height: 20 }} />}
            <Subtitle1>
                <strong>Action Items</strong>
            </Subtitle1>
            {actionItems === undefined ? (
                <Spinner />
            ) : (
                <Body1>
                    {actionItems.length > 0 ? formatActionItems(actionItems) : "We didn't find any action items."}
                </Body1>
            )}
            <br />
            <br />
            <Button style={{ width: 54 }} appearance="secondary" onClick={() => onBack()}>
                Back
            </Button>
        </div>
    );
};

export default AISummary;
