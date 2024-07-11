// Copyright (c) Microsoft. All rights reserved.

import { Body1, Button, Image, Textarea, Title3 } from '@fluentui/react-components';
import React, { FC } from 'react';
import wordLogo from '../../src/word.png';
import { useSemanticKernel } from '../hooks/useSemanticKernel';
import { IKeyConfig } from '../model/KeyConfig';
import InteractionButton from './InteractionButton';

interface IData {
    uri: string;
    config: IKeyConfig;
    onBack: () => void;
}

const InteractWithGraph: FC<IData> = ({ uri, config, onBack }) => {
    const sk = useSemanticKernel(uri);
    const defaultText = `A glacier is a persistent body of dense ice that is constantly moving under its own weight. A glacier forms where the accumulation of snow exceeds its ablation over many years, often centuries. It acquires distinguishing features, such as crevasses and seracs, as it slowly flows and deforms under stresses induced by its weight. As it moves, it abrades rock and debris from its substrate to create landforms such as cirques, moraines, or fjords. Although a glacier may flow into a body of water, it forms only on land and is distinct from the much thinner sea ice and lake ice that form on the surface of bodies of water.`;
    const filename = 'AuthenticationSampleSummary.docx';
    const path = '%temp%\\' + filename;
    const destinationPath = '/' + filename;

    const [text, setText] = React.useState(defaultText);

    const runTask1 = async () => {
        try {
            //get summary
            var summary = await sk.invokeAsync(config, { value: text }, 'summarizeskill', 'summarize');

            //write document
            await sk.invokeAsync(
                config,
                {
                    value: summary.value,
                    inputs: [{ key: 'filePath', value: path }],
                },
                'documentskill',
                'appendtext',
            );

            //upload to onedrive
            await sk.invokeAsync(
                config,
                {
                    value: path,
                    inputs: [{ key: 'destinationPath', value: destinationPath }],
                },
                'clouddriveskill',
                'uploadfile',
            );
        } catch (e) {
            alert('Something went wrong.\n\nDetails:\n' + e);
        }
    };

    const runTask2 = async () => {
        try {
            var shareLink = await sk.invokeAsync(
                config,
                { value: destinationPath },
                'clouddriveskill',
                'createlink',
            );
            var myEmail = await sk.invokeAsync(config, { value: '' }, 'emailskill', 'getmyemailaddress');

            await sk.invokeAsync(
                config,
                {
                    value: `Here's the link: ${shareLink.value}\n\nReminder: Please delete the document on your OneDrive after you finish with this sample app.`,
                    inputs: [
                        {
                            key: 'recipients',
                            value: myEmail.value,
                        },
                        {
                            key: 'subject',
                            value: 'Semantic Kernel Authentication Sample Project Document Link',
                        },
                    ],
                },
                'emailskill',
                'sendemail',
            );
        } catch (e) {
            alert('Something went wrong.\n\nDetails:\n' + e);
        }
    };

    const runTask3 = async () => {
        try {
            var reminderDate = new Date();
            reminderDate.setDate(reminderDate.getDate() + 3);

            await sk.invokeAsync(
                config,
                {
                    value: 'Remind me to follow up re the authentication sample email',
                    inputs: [
                        {
                            key: 'reminder',
                            value: reminderDate.toISOString(),
                        },
                    ],
                },
                'tasklistskill',
                'addtask',
            );
        } catch (e) {
            alert('Something went wrong.\n\nDetails:\n' + e);
        }
    };

    return (
        <div style={{ padding: 40, gap: 10, display: 'flex', flexDirection: 'column', alignItems: 'left' }}>
            <Title3>Interact with data and services</Title3>
            <Body1>
                You can interact with data and Microsoft services for your account. Ask questions about your data or ask
                for help to complete a task.
            </Body1>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 30, paddingTop: 30 }}>
                <div style={{ display: 'flex', flexDirection: 'row', gap: 7.25, alignItems: 'left' }}>
                    <Image src={wordLogo} width={24} />
                    <Body1>Sample Doc: {filename}</Body1>
                </div>

                <Textarea
                    appearance="filled-lighter-shadow"
                    textarea={{ style: { height: 306 } }}
                    style={{ maxWidth: 761 }}
                    resize="vertical"
                    value={text}
                    onChange={(e, d) => setText(d.value)}
                />
                <InteractionButton
                    taskDescription="Summarize the above into a new Word Document and save it on OneDrive"
                    runTask={runTask1}
                />

                <InteractionButton
                    taskDescription="Get a shareable link and email the link to myself"
                    runTask={runTask2}
                />
                <InteractionButton
                    taskDescription="Add a reminder to follow-up with the email sent above"
                    runTask={runTask3}
                />
            </div>
            <br />
            <Button style={{ width: 54 }} appearance="secondary" onClick={() => onBack()}>
                Back
            </Button>
        </div>
    );
};

export default InteractWithGraph;
