// Copyright (c) Microsoft. All rights reserved.

import { Body1, Button, Input, Label, Radio, RadioGroup, Spinner, Title3 } from '@fluentui/react-components';
import { FC, useState } from 'react';
import { useSemanticKernel } from '../hooks/useSemanticKernel';
import { IAsk, IAskInput } from '../model/Ask';
import { IKeyConfig } from '../model/KeyConfig';

interface IData {
    uri: string;
    keyConfig: IKeyConfig;
    onTopicSelected: (title: string, detail: string) => void;
    onBack: () => void;
}

interface ITopicWithSummary {
    title: string;
    description: string;
}

const TopicSelection: FC<IData> = ({ uri, keyConfig, onTopicSelected, onBack }) => {
    const sk = useSemanticKernel(uri);
    const [topic, setTopic] = useState<string>('');
    const [topics, setTopics] = useState<ITopicWithSummary[]>();
    const [fetchingTopics, setFetchingTopics] = useState<boolean>();
    const [selectedTopicIndex, setSelectedTopicIndex] = useState<number>(0);

    const fetchTopics = async () => {
        if (topic === undefined) {
            return;
        }

        setFetchingTopics(true);

        var askInputs: IAskInput[] = [
            {
                key: 'numIdeas',
                value: '4',
            },
        ];

        var ask: IAsk = { value: topic, inputs: askInputs };

        try {
            var result = await sk.invokeAsync(keyConfig, ask, 'childrensbookskill', 'bookideas');
            var jsonValue = (result.value as string).substring(
                (result.value as string).indexOf('['),
                (result.value as string).indexOf(']') + 1,
            );
            var results = JSON.parse(jsonValue);
            var topics: ITopicWithSummary[] = [];

            for (var r of results) {
                topics.push({
                    title: r.title,
                    description: r.description,
                });
            }
            setTopics(topics);
        } catch (e) {
            alert('Something went wrong.\n\nDetails:\n' + e);
        }

        setFetchingTopics(false);
    };

    return (
        <div style={{ padding: 80, gap: 20, display: 'flex', flexDirection: 'column', alignItems: 'left' }}>
            <Title3>Enter a topic to generate ideas</Title3>
            <Body1>
                Start by entering a topic and a list of ideas will be generated for a children's book. Select your
                favorite idea to move to the next step, creating the book.
            </Body1>
            <Body1>
                <strong>What's the book topic on your mind?</strong>
            </Body1>
            <div style={{ gap: 20, display: 'flex', flexDirection: 'row', alignItems: 'left' }}>
                <Input
                    style={{ minWidth: 500, height: 36 }}
                    size="medium"
                    appearance="outline"
                    onKeyUp={(e) => {
                        if (e.key === 'Enter') {
                            fetchTopics();
                        }
                    }}
                    value={topic}
                    onChange={(e, d) => setTopic(d.value)}
                    placeholder="Type a book topic for a children's book. Example: cup, dragon, cookies..."
                />
                <Button appearance="primary" onClick={() => fetchTopics()}>
                    Get Ideas
                </Button>
            </div>

            {fetchingTopics ? (
                <Spinner />
            ) : (
                <div style={{ gap: 20, display: 'flex', flexDirection: 'row', alignItems: 'left', flexWrap: 'wrap' }}>
                    {topics === undefined ? (
                        <></>
                    ) : (
                        <div style={{ gap: 20, display: 'flex', flexDirection: 'column' }}>
                            <Label weight="semibold">
                                Here are the generated ideas. Which one would you like to choose for your book?
                            </Label>
                            <RadioGroup
                                required
                                value={'' + selectedTopicIndex}
                                onChange={(_, data) => setSelectedTopicIndex(+data.value)}
                            >
                                <div style={{ gap: 20, display: 'flex', flexDirection: 'column' }}>
                                    {topics?.map((t, idx) => (
                                        <Radio
                                            key={idx}
                                            value={'' + idx}
                                            label={
                                                <div style={{ gap: 10, display: 'flex', flexDirection: 'column' }}>
                                                    <Body1>{t.title}</Body1>
                                                    <Body1>{t.description}</Body1>
                                                </div>
                                            }
                                        />
                                    ))}
                                </div>
                            </RadioGroup>
                        </div>
                    )}
                </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'row', alignItems: 'left', gap: 20 }}>
                <Button appearance="secondary" onClick={() => onBack()}>
                    Back
                </Button>
                <Button
                    appearance="primary"
                    disabled={topics === undefined}
                    onClick={() => {
                        if (topics !== undefined)
                            onTopicSelected(topics[selectedTopicIndex].title, topics[selectedTopicIndex].description);
                    }}
                >
                    Create Book
                </Button>
            </div>
        </div>
    );
};

export default TopicSelection;
