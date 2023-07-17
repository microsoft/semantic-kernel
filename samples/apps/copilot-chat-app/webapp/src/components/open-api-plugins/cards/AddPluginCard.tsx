import { makeStyles, tokens } from '@fluentui/react-components';
import AddPluginIcon from '../../../assets/plugin-icons/add-plugin.png';
import { PluginWizard } from '../plugin-wizard/PluginWizard';
import { BaseCard } from './BaseCard';

const useClasses = makeStyles({
    root: {
        marginBottom: tokens.spacingVerticalXXL,
    },
});

export const AddPluginCard: React.FC = () => {
    const classes = useClasses();

    return (
        <div className={classes.root}>
            <BaseCard
                image={AddPluginIcon}
                header="Custom Plugin"
                secondaryText="AI Developer"
                description="Add your own ChatGPT compatible plugin."
                action={<PluginWizard />}
                helpText="Want to learn how to create a custom plugin?"
                helpLink="https://aka.ms/sk-plugins-howto"
            />
        </div>
    );
};
