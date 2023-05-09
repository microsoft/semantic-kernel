import { Button, Text, makeStyles, shorthands } from '@fluentui/react-components';
import { useState } from 'react';
import { IPlan, IPlanStep } from '../../../libs/models/Plan';
import { PlanStepCard } from './PlanStepCard';

const useClasses = makeStyles({
    container: {
        ...shorthands.gap('11px'),
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'baseline',
    },
    buttons: {
        display: 'flex',
        flexDirection: 'row',
        marginTop: '12px',
        marginBottom: '12px',
        ...shorthands.gap('16px'),
    },
});

interface PlanViewerProps {
    plan: IPlan;
    actionRequired?: boolean;
    onSubmit: () => Promise<void>;
    onCancel: () => Promise<void>;
}

export const PlanViewer: React.FC<PlanViewerProps> = ({ plan, actionRequired, onSubmit, onCancel }) => {
    const classes = useClasses();
    var stepCount = 1;

    const [showButtons, setShowButtons] = useState(actionRequired);

    const onCancelClick = () => {
        setShowButtons(false);
        onCancel();
    };

    const onProceedClick = () => {
        setShowButtons(false);
        onSubmit();
    };

    return (
        <div className={classes.container}>
            <Text>Based on the request, Copilot Chat will run the following steps:</Text>
            <Text weight="bold">{`Goal: ${plan.description}`}</Text>
            {plan.steps.map((step: IPlanStep) => (
                <PlanStepCard index={stepCount++} step={step} />
            ))}
            {showButtons && (
                <>
                    Would you like to proceed with the plan?
                    <div className={classes.buttons}>
                        <Button appearance="secondary" onClick={onCancelClick}>
                            No, cancel plan
                        </Button>
                        <Button type="submit" appearance="primary" onClick={onProceedClick}>
                            Yes, proceed
                        </Button>
                    </div>
                </>
            )}
        </div>
    );
};
