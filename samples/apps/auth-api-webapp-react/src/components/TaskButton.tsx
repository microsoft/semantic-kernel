// Copyright (c) Microsoft. All rights reserved.

import { Body1, Button, Spinner } from '@fluentui/react-components';
import { CheckmarkCircle24Regular, PlayCircle24Regular } from '@fluentui/react-icons';
import { FC, useState } from 'react';
import { useSemanticKernel } from '../hooks/useSemanticKernel';
import { IAsk, IAskInput } from '../model/Ask';
import { IAskResult } from '../model/AskResult';
import { IKeyConfig } from '../model/KeyConfig';

export interface ITask {
    skillName: string;
    functionName: string;
    ask: IAsk;
}

interface IData {
    taskDescription: string;
    keyConfig: IKeyConfig;
    uri: string;
    input: string;
    skills?: string[];
    onTaskComplete: (result: IAskResult) => void;
}

const TaskButton: FC<IData> = ({ taskDescription, onTaskComplete, keyConfig, uri, input, skills }) => {
    const sk = useSemanticKernel(uri);
    const [isBusy, setIsBusy] = useState<boolean>(false);
    const [canRunTask, setCanRunTask] = useState<boolean>(true);

    const runTask = async () => {
        setIsBusy(true);

        try {
            var createPlanResult = await sk.createPlanAsync(keyConfig, {
                value: `${input}\n${taskDescription}`,
                skills: skills,
            });

            console.log(createPlanResult);

            var inputs: IAskInput[] = [...createPlanResult.state];

            var executePlanResult = await sk.executePlanAsync(keyConfig, {
                inputs: inputs,
                value: createPlanResult.value,
            });

            onTaskComplete(executePlanResult);
        } catch (e) {
            alert('Unable to complete task.\n\nDetails:\n' + e);
        }

        setIsBusy(false);
    };

    return (
        <>
            <div style={{ display: 'flex', flexDirection: 'row', alignItems: 'center' }}>
                <Button
                    disabled={!canRunTask}
                    appearance="transparent"
                    size="small"
                    onClick={() => {
                        setCanRunTask(false);
                        runTask();
                    }}
                >
                    {!canRunTask ? (
                        <CheckmarkCircle24Regular primaryFill="green" filled={true} />
                    ) : (
                        <PlayCircle24Regular />
                    )}
                </Button>
                <Body1>{taskDescription}</Body1>
            </div>
            {isBusy ? <Spinner /> : null}
        </>
    );
};

export default TaskButton;
