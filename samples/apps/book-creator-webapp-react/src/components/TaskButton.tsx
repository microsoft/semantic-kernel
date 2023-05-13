// Copyright (c) Microsoft. All rights reserved.

import { Body1, Button, Spinner } from '@fluentui/react-components';
import { CheckmarkCircle24Regular, PlayCircle24Regular } from '@fluentui/react-icons';
import { FC, useState } from 'react';
import { useSemanticKernel } from '../hooks/useSemanticKernel';
import { useTaskRunner } from '../hooks/useTaskRunner';
import { IAsk } from '../model/Ask';
import { IKeyConfig } from '../model/KeyConfig';
export interface ITask {
    skillName: string;
    functionName: string;
    ask: IAsk;
}

interface IData {
    taskDescription: string;
    taskResponseFormat?: string;
    taskTitle: string;
    keyConfig: IKeyConfig;
    uri: string;
    skills?: string[];
    onPlanCreated?: (ask: IAsk, plan: string) => void;
    onTaskCompleted: (ask: IAsk, result: string) => void;
}

const TaskButton: FC<IData> = ({
    taskTitle,
    taskDescription,
    taskResponseFormat,
    onTaskCompleted,
    onPlanCreated,
    keyConfig,
    uri,
    skills,
}) => {
    const maxSteps = 10; //this is the maximum number of iterations planner will take while attempting to solve
    const sk = useSemanticKernel(uri);
    const taskRunner = useTaskRunner(sk, keyConfig, maxSteps);
    const [isBusy, setIsBusy] = useState<boolean>(false);
    const [canRunTask, setCanRunTask] = useState<boolean>(true);

    const runTask = async () => {
        setIsBusy(true);

        try {
            await taskRunner.runTask(taskDescription, taskResponseFormat, skills, onPlanCreated, onTaskCompleted);
        } catch (e) {
            alert('Something went wrong.\n\nDetails:\n' + e);
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
                <Body1>{taskTitle}</Body1>
            </div>
            {isBusy ? <Spinner /> : null}
        </>
    );
};

export default TaskButton;
