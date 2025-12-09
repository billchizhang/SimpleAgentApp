from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Step:
    """Represents a single step in the ReAct loop."""
    step_number: int
    step_type: str  # "load_registry", "thought", "action", "observation", "final_answer", "error"
    description: str
    timestamp: str
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ResponseFormatter:
    """
    Formats agent execution steps and final responses.

    This class manages the recording of all steps taken during agent execution,
    including ReAct-style reasoning (Thought, Action, Observation) and generates
    the final response with complete execution trace.
    """

    def __init__(self):
        self.steps: List[Step] = []
        self.step_counter = 0

    def add_step(
        self,
        step_type: str,
        description: str,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Add a new step to the execution trace.

        Args:
            step_type: Type of step (load_registry, thought, action, observation, final_answer, error)
            description: Human-readable description of the step
            details: Optional dictionary with step-specific details
            error: Optional error message if the step encountered an error
        """
        self.step_counter += 1
        step = Step(
            step_number=self.step_counter,
            step_type=step_type,
            description=description,
            timestamp=datetime.now().isoformat(),
            details=details,
            error=error
        )
        self.steps.append(step)

    def format_final_response(
        self,
        answer: str,
        success: bool = True,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create the final response dictionary with all execution steps.

        Args:
            answer: The final answer to return to the user
            success: Whether the query was processed successfully
            error: Optional error message for the overall execution

        Returns:
            Dictionary containing:
                - success: bool
                - answer: str (final answer to user)
                - steps: List[Dict] (all steps taken, serialized)
                - error: Optional[str] (if any error occurred)
        """
        return {
            "success": success,
            "answer": answer,
            "steps": [asdict(step) for step in self.steps],
            "error": error
        }

    def get_steps_summary(self) -> str:
        """
        Generate a human-readable summary of all steps.

        Returns:
            Multi-line string summarizing the execution steps
        """
        summary_lines = [f"Execution Summary ({len(self.steps)} steps):"]
        for step in self.steps:
            prefix = "✓" if not step.error else "✗"
            summary_lines.append(f"  {prefix} Step {step.step_number}: {step.description}")
            if step.error:
                summary_lines.append(f"      Error: {step.error}")
        return "\n".join(summary_lines)

    def get_steps(self) -> List[Dict[str, Any]]:
        """
        Get all steps as a list of dictionaries.

        Returns:
            List of step dictionaries, suitable for JSON serialization
        """
        return [asdict(step) for step in self.steps]

    def get_step_count(self) -> int:
        """Return the total number of steps recorded."""
        return len(self.steps)

    def get_steps_by_type(self, step_type: str) -> List[Step]:
        """
        Get all steps of a specific type.

        Args:
            step_type: The type of steps to retrieve

        Returns:
            List of Step objects matching the given type
        """
        return [step for step in self.steps if step.step_type == step_type]
