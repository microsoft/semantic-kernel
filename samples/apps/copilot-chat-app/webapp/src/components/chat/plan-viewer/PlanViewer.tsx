import { Button, Text, makeStyles, mergeClasses, shorthands } from '@fluentui/react-components';
import { CheckmarkCircle24Regular, DismissCircle24Regular } from '@fluentui/react-icons';
import { ChatMessageState } from '../../../libs/models/ChatMessage';
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
    status: {
        ...shorthands.gap('10px'),
    },
    text: {
        alignSelf: 'center',
    },
});

interface PlanViewerProps {
    plan: IPlan;
    planState: ChatMessageState;
    onSubmit: () => Promise<void>;
    onCancel: () => Promise<void>;
}

export const PlanViewer: React.FC<PlanViewerProps> = ({ plan, planState, onSubmit, onCancel }) => {
    const classes = useClasses();
    var stepCount = 1;

    return (
        <div className={classes.container}>
            <Text>Based on the request, Copilot Chat will run the following steps:</Text>
            <Text weight="bold">{`Goal: ${plan.description}`}</Text>
            {plan.steps.map((step: IPlanStep) => {
                const stepIndex = stepCount++;
                return <PlanStepCard key={`Plan step: ${stepIndex}`} index={stepIndex} step={step} />;
            })}
            {planState === ChatMessageState.PlanApprovalRequired && (
                <>
                    Would you like to proceed with the plan?
                    <div className={classes.buttons}>
                        <Button appearance="secondary" onClick={onCancel}>
                            No, cancel plan
                        </Button>
                        <Button type="submit" appearance="primary" onClick={onSubmit}>
                            Yes, proceed
                        </Button>
                    </div>
                </>
            )}
            {planState === ChatMessageState.PlanApproved && (
                <div className={mergeClasses(classes.buttons, classes.status)}>
                    <CheckmarkCircle24Regular />
                    <Text className={classes.text}> Plan Executed</Text>
                </div>
            )}
            {planState === ChatMessageState.PlanRejected && (
                <div className={mergeClasses(classes.buttons, classes.status)}>
                    <DismissCircle24Regular />
                    <Text className={classes.text}> Plan Cancelled</Text>
                </div>
            )}
        </div>
    );
};
