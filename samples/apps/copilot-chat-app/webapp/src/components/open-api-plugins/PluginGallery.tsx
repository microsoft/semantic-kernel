import {
    Body1,
    Button,
    Dialog,
    DialogBody,
    DialogContent,
    DialogSurface,
    DialogTitle,
    DialogTrigger,
    Subtitle1,
    Subtitle2,
    makeStyles,
    shorthands,
} from '@fluentui/react-components';
import { AppsAddIn24Regular, Dismiss24Regular } from '@fluentui/react-icons';
import { useState } from 'react';
import { useAppSelector } from '../../redux/app/hooks';
import { RootState } from '../../redux/app/store';
import { PluginCard } from './PluginCard';

const useClasses = makeStyles({
    root: {
        maxWidth: '1052px',
        height: '632px',
        width: 'fit-content',
    },
    title: {
        ...shorthands.margin(0, 0, '12px'),
    },
    description: {
        ...shorthands.margin(0, 0, '12px'),
    },
    content: {
        display: 'flex',
        flexDirection: 'row',
        flexWrap: 'wrap',
        rowGap: '24px',
        columnGap: '24px',
        ...shorthands.margin(0, '2px', '12px'),
    },
});

export const PluginGallery: React.FC = () => {
    const classes = useClasses();

    const plugins = useAppSelector((state: RootState) => state.plugins);
    const [open, setOpen] = useState(false);

    return (
        <Dialog open={open} onOpenChange={(_event, data) => setOpen(data.open)}>
            <DialogTrigger>
                <Button appearance="transparent" icon={<AppsAddIn24Regular color="white" />} />
            </DialogTrigger>
            <DialogSurface className={classes.root}>
                <DialogBody>
                    <DialogTitle
                        action={
                            <DialogTrigger action="close">
                                <Button appearance="subtle" aria-label="close" icon={<Dismiss24Regular />} />
                            </DialogTrigger>
                        }
                    >
                        <Subtitle1 block className={classes.title}>
                            Enable Copilot Chat Plugins
                        </Subtitle1>
                        <Body1 as="p" block className={classes.description}>
                            Authorize plugins and have more powerful bots!
                        </Body1>
                    </DialogTitle>
                    <DialogContent>
                        <Subtitle2 block className={classes.title}>
                            Available Plugins
                        </Subtitle2>{' '}
                        <div className={classes.content}>
                            {Object.entries(plugins).map((entry) => {
                                const plugin = entry[1];
                                return <PluginCard key={plugin.name} plugin={plugin} />;
                            })}
                        </div>
                    </DialogContent>
                </DialogBody>
            </DialogSurface>
        </Dialog>
    );
};
