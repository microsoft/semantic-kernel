// Copyright (c) Microsoft. All rights reserved.

import {
    Body1,
    Button,
    Menu,
    MenuItem,
    MenuList,
    MenuPopover,
    MenuTrigger,
    Spinner,
    Subtitle1,
    Subtitle2,
    Title3,
} from '@fluentui/react-components';
import { Book24Regular, Code24Regular, Thinking24Regular } from '@fluentui/react-icons';
import { FC, useState } from 'react';
import { useSemanticKernel } from '../hooks/useSemanticKernel';
import { IAsk, IAskInput } from '../model/Ask';
import { IKeyConfig } from '../model/KeyConfig';
import TaskButton from './TaskButton';

interface IData {
    uri: string;
    title: string;
    description: string;
    keyConfig: IKeyConfig;
    onBack: () => void;
}

interface IPage {
    num: number;
    content: string;
}

interface IResult {
    outline: string;
    summary: string;
    pages: IPage[];
}

interface IProcessHistory {
    uri: string;
    functionName: string;
    input: string;
    timestamp: string;
}

enum BookCreationState {
    Ready = 0,
    GetNovelOutline = 1,
    GetSummaryOfOutline = 2,
    ReadyToCreateBookFromOutline = 3,
    CreateBookFromOutline = 4,
    Complete = 5,
}

const CreateBookWithPlanner: FC<IData> = ({ uri, title, description, keyConfig, onBack }) => {
    const sk = useSemanticKernel(uri);
    const bookJsonFormat = "{'pages': [{'num':0, content:''}]}"; //the format we will ask planner to return results in

    const [bookCreationState, setBookCreationState] = useState<BookCreationState>(BookCreationState.Ready);
    const [busyMessage, setBusyMessage] = useState<string>('');
    const [bookState, setBookState] = useState<IResult>({} as IResult);
    const [showProcess, setShowProcess] = useState<boolean>(false);
    const [processHistory, setProcessHistory] = useState<IProcessHistory[]>([]);

    const translate = async (text: string, inputs: IAskInput[]) => {
        var ask: IAsk = { value: text, inputs: inputs };

        try {
            var result = await sk.invokeAsync(keyConfig, ask, 'writerskill', 'translate');

            var historyItem = {
                functionName: 'translate',
                input: JSON.stringify(ask),
                timestamp: new Date().toTimeString(),
                uri: '/api/skills/writerskill/invoke/translate',
            };
            setProcessHistory((processHistory) => [...processHistory, historyItem]);
            return result.value;
        } catch (e) {
            alert('Something went wrong.\n\nDetails:\n' + e);
        }
    };

    const rewrite = async (text: string, inputs: IAskInput[]) => {
        var ask: IAsk = { value: text, inputs: inputs };

        try {
            var result = await sk.invokeAsync(keyConfig, ask, 'writerskill', 'rewrite');

            var historyItem = {
                functionName: 'rewrite',
                input: JSON.stringify(ask),
                timestamp: new Date().toTimeString(),
                uri: '/api/skills/writerskill/invoke/rewrite',
            };
            setProcessHistory((processHistory) => [...processHistory, historyItem]);
            return result.value;
        } catch (e) {
            alert('Something went wrong.\n\nDetails:\n' + e);
        }
    };

    const translateTo = async (language: string) => {
        setBusyMessage(`Translating to ${language}`);

        if (bookState.pages !== undefined) {
            var translatedPages: IPage[] = [];

            for (var p of bookState.pages) {
                var translatedPage = await translate(p.content, [{ key: 'language', value: language }]);
                translatedPages.push({ content: translatedPage!, num: p.num });
            }

            setBookState((bookState) => ({ ...bookState, pages: translatedPages }));
        }

        setBusyMessage('');
        setIsTranslated(!isTranslated);
    };

    const rewriteAs = async (style: string) => {
        var inputs: IAskInput[] = [
            {
                key: 'style',
                value: style,
            },
        ];

        setBusyMessage(`Rewriting in the style of ${style}`);

        if (bookState.pages !== undefined) {
            var rewrittenPages: IPage[] = [];

            for (var p of bookState.pages) {
                var rewrittenPage = await rewrite(p.content, inputs);
                rewrittenPages.push({ content: rewrittenPage!, num: p.num });
            }

            setBookState((bookState) => ({ ...bookState, pages: rewrittenPages }));
        }

        var rewrittenOutline = await rewrite(bookState.outline, inputs);
        var rewrittenSummary = await rewrite(bookState.summary, inputs);

        setBookState((bookState) => ({ ...bookState, outline: rewrittenOutline!, summary: rewrittenSummary! }));
        setBusyMessage('');
    };

    const onPlanCreated = (ask: IAsk, plan: string) => {
        var historyItem = {
            functionName: 'createplan',
            input: JSON.stringify(ask),
            timestamp: new Date().toTimeString(),
            uri: '/api/planner/createplan',
        };
        setProcessHistory((processHistory) => [...processHistory, historyItem]);
    };

    // TODO: refactor to support ambiguous return types (required to enable SequentialPlanner)
    const onTaskCompleted = (ask: IAsk, result: string, variables?: IAskInput[]) => {
        var historyItem = {
            functionName: 'executeplan',
            input: JSON.stringify(ask),
            timestamp: new Date().toTimeString(),
            uri: '/api/planner/execute',
        };
        setProcessHistory((processHistory) => [...processHistory, historyItem]);

        var jsonValue = result.substring(result.indexOf('['), result.indexOf(']') + 1);
        var results = JSON.parse(jsonValue);

        var pages: IPage[] = [];

        for (var r of results) {
            pages.push({
                content: r.content,
                num: r.page,
            });
        }

        setBookState((bookState) => ({ ...bookState, pages: pages }));
        setBookCreationState(BookCreationState.Complete);
    };

    const [isTranslated, setIsTranslated] = useState<boolean>(false);
    const baseLanguage = 'English';
    const translateToLanguage = 'Spanish';
    const rewriteAsStyle = 'a surfer';

    return (
        <div style={{ padding: 40, gap: 10, display: 'flex', flexDirection: 'column', alignItems: 'left' }}>
            <Title3>Create your book "{title}"</Title3>
            <Subtitle2>Run each ask on the page to see the steps that will execute</Subtitle2>

            <div style={{ gap: 20, display: 'flex', flexDirection: 'column', alignItems: 'left' }}>
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <TaskButton
                        keyConfig={keyConfig}
                        skills={['writerskill', 'childrensbookskill', 'summarizeskill']}
                        uri={uri}
                        onPlanCreated={onPlanCreated}
                        onTaskCompleted={onTaskCompleted}
                        taskTitle="Create an 8 page children's book based on the topic summary from the previous page"
                        taskDescription={`Create an 8 page children's book called ${title} about: ${description}`}
                        taskResponseFormat={bookJsonFormat}
                    />
                </div>
                <div style={{ minWidth: 300, maxWidth: 800, gap: 10, display: 'flex', flexDirection: 'column' }}>
                    <div
                        style={{
                            gap: 10,
                            display: 'flex',
                            flexDirection: 'row',
                            alignSelf: 'stretch',
                            justifyContent: 'space-between',
                        }}
                    >
                        <Subtitle1>Results:</Subtitle1>
                        <div>
                            <Menu>
                                <MenuTrigger disableButtonEnhancement>
                                    <Button
                                        disabled={bookCreationState === BookCreationState.Ready}
                                        icon={<Thinking24Regular />}
                                    >
                                        Rethink
                                    </Button>
                                </MenuTrigger>

                                <MenuPopover>
                                    <MenuList>
                                        <MenuItem
                                            onClick={() =>
                                                translateTo(isTranslated ? baseLanguage : translateToLanguage)
                                            }
                                        >
                                            Translate to {isTranslated ? baseLanguage : translateToLanguage}
                                        </MenuItem>
                                        <MenuItem onClick={() => rewriteAs(rewriteAsStyle)}>
                                            Rewrite in the style of {rewriteAsStyle}
                                        </MenuItem>
                                    </MenuList>
                                </MenuPopover>
                            </Menu>
                            <Button
                                icon={showProcess ? <Book24Regular /> : <Code24Regular />}
                                onClick={() => setShowProcess(!showProcess)}
                            >
                                {showProcess ? 'Show book' : 'Show process'}
                            </Button>
                        </div>
                    </div>

                    {showProcess ? (
                        <>
                            <div
                                style={{
                                    gap: 5,
                                    width: 700,
                                    height: 500,
                                    padding: 40,
                                    overflowY: 'scroll',
                                    boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.14), 0px 0px 2px rgba(0, 0, 0, 0.12)',
                                    borderRadius: 4,
                                }}
                            >
                                {processHistory.map((h, idx) => (
                                    <div key={idx}>
                                        <strong>[{h.timestamp}]</strong>
                                        <br />
                                        Invoked function: <em>{h.functionName}</em> at URI: <em>{h.uri}</em> with ask:
                                        <br />
                                        <br />
                                        {h.input}
                                        <br />
                                        <br />
                                        <hr />
                                        <br />
                                    </div>
                                ))}
                            </div>
                        </>
                    ) : (
                        <div
                            style={{
                                gap: 5,
                                width: 700,
                                height: 500,
                                padding: 40,
                                overflowY: 'scroll',
                                boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.14), 0px 0px 2px rgba(0, 0, 0, 0.12)',
                                borderRadius: 4,
                            }}
                        >
                            {busyMessage.length > 0 ? (
                                <Spinner style={{ padding: 40 }} labelPosition="after" label={busyMessage} />
                            ) : null}
                            {bookState === undefined ? null : (
                                <>
                                    {bookState.pages !== undefined && bookState.pages.length > 0
                                        ? bookState.pages.map((p, idx) => (
                                              <div
                                                  key={idx}
                                                  style={{ display: 'flex', gap: 5, flexDirection: 'column' }}
                                              >
                                                  <Body1>Page {p.num}</Body1>
                                                  <Body1>{p.content}</Body1>
                                                  <hr />
                                              </div>
                                          ))
                                        : null}
                                </>
                            )}
                        </div>
                    )}
                </div>
            </div>
            <Button appearance="secondary" size="medium" style={{ width: 54 }} onClick={() => onBack()}>
                Back
            </Button>
        </div>
    );
};

export default CreateBookWithPlanner;
