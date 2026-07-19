"""Loads and validates workflow YAML into models.workflows.WorkflowDefinition. The
model layer never invents workflow steps — this is the only place a workflow is
parsed, and it rejects anything that doesn't validate."""
from __future__ import annotations

import os

import yaml
from pydantic import ValidationError

from models.workflows import WorkflowDefinition

_WORKFLOWS_DIR = os.path.dirname(os.path.abspath(__file__))


class WorkflowLoadError(RuntimeError):
    pass


def load_workflow(workflow_id: str) -> WorkflowDefinition:
    path = os.path.join(_WORKFLOWS_DIR, f"{workflow_id}.yaml")
    if not os.path.exists(path):
        raise WorkflowLoadError(f"No workflow file for '{workflow_id}' at {path}")

    with open(path, "r") as f:
        raw = yaml.safe_load(f)

    try:
        workflow = WorkflowDefinition.model_validate(raw)
    except ValidationError as e:
        raise WorkflowLoadError(f"Workflow '{workflow_id}' failed schema validation: {e}") from e

    if workflow.workflow_id != workflow_id:
        raise WorkflowLoadError(
            f"workflow_id in file ({workflow.workflow_id!r}) does not match requested id ({workflow_id!r})"
        )

    step_ids = [s.step_id for s in workflow.examination_procedures]
    if len(step_ids) != len(set(step_ids)):
        raise WorkflowLoadError(f"Duplicate step_id in workflow '{workflow_id}'")

    known_ids = set(step_ids)
    for goal_id in workflow.initial_goals:
        if goal_id not in known_ids:
            raise WorkflowLoadError(
                f"initial_goals references unknown step_id '{goal_id}' not in examination_procedures"
            )

    return workflow


def is_known_step(workflow: WorkflowDefinition, step_id: str) -> bool:
    """Used by the state tracker to reject a model proposing an invented step ID."""
    return step_id in workflow.step_ids()
