// Copyright (c) Microsoft. All rights reserved.

import { Button, Popover, PopoverSurface, PopoverTrigger, Textarea, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { AlertType } from '../../../libs/models/AlertType';
import { useAppDispatch } from '../../../redux/app/hooks';
import { addAlert } from '../../../redux/features/app/appSlice';
import { Info16 } from '../../shared/BundledIcons';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        ...shorthands.gap(tokens.spacingVerticalSNudge),
    },
    horizontal: {
        display: 'flex',
        ...shorthands.gap(tokens.spacingVerticalSNudge),
        alignItems: 'center',
    },
    controls: {
        display: 'flex',
        marginLeft: 'auto',
    },
});

interface PromptEditorProps {
    title: string;
    prompt: string;
    isEditable: boolean;
    info: string;
    modificationHandler?: (value: string) => Promise<void>;
}

export const PromptEditor: React.FC<PromptEditorProps> = ({
    title,
    prompt,
    isEditable,
    info,
    modificationHandler,
}) => {
    const classes = useClasses();
    const dispatch = useAppDispatch();
    const [value, setValue] = React.useState<string>(prompt);

    React.useEffect(() => {
        setValue(prompt);
    }, [prompt]);

    const onSaveButtonClick = () => {
        if (modificationHandler) {
            modificationHandler(value).catch((error) => {
                setValue(prompt);
                const message = `Error saving the new prompt: ${(error as Error).message}`;
                dispatch(
                    addAlert({
                        type: AlertType.Error,
                        message,
                    }),
                );
            });
        }
    };

    return (
        <div className={classes.root}>
            <div className={classes.horizontal}>
                <h3>{title}</h3>
                <Popover withArrow>
                        <PopoverTrigger disableButtonEnhancement>
                            <Button icon={<Info16 />} appearance="transparent" />
                        </PopoverTrigger>
                        <PopoverSurface>
                            {info}
                        </PopoverSurface>
                    </Popover>
            </div>
            <Textarea
                resize="vertical"
                value={value}
                disabled={!isEditable}
                onChange={(_event, data) => {
                    setValue(data.value);
                }}
            />
            {isEditable &&
                <div className={classes.controls}>
                    <Button onClick={() => onSaveButtonClick()}>
                        Save
                    </Button>
                </div>
            }
        </div>
    );
};
