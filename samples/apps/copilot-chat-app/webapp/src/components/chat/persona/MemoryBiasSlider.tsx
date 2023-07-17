// Copyright (c) Microsoft. All rights reserved.

import { Button, Label, Popover, PopoverSurface, PopoverTrigger, Slider, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { Info16 } from '../../shared/BundledIcons';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
    },
    horizontal: {
        display: 'flex',
        ...shorthands.gap(tokens.spacingVerticalSNudge),
        alignItems: 'center',
    },
    content: {
        display: 'flex',
        flexDirection: 'column',
        ...shorthands.gap(tokens.spacingHorizontalS),
        paddingBottom: tokens.spacingHorizontalM,
    },
    popover: {
        width: '300px',
    },
    header: {
        marginBlockEnd: tokens.spacingHorizontalM,
    },
});


export const MemoryBiasSlider: React.FC = () => {
    const classes = useClasses();

    return (
        <div className={classes.root}>
            <div className={classes.horizontal}>
                <h3>Memory Bias</h3>
                <Popover withArrow>
                        <PopoverTrigger disableButtonEnhancement>
                            <Button icon={<Info16 />} appearance="transparent" />
                        </PopoverTrigger>
                        <PopoverSurface>
                            This is a slider that allows the user to bias the chat bot towards short or long term memory.
                        </PopoverSurface>
                    </Popover>
            </div>
            <div>
                <Label>Short Term</Label>
                <Slider min={0} max={100} defaultValue={50} />
                <Label>Long Term</Label>
            </div>
        </div>
    );
};
