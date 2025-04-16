from abc import ABC, abstractmethod
from pr_agent.task import PRTask
from typing import Optional, List
from pr_agent.prompting.prompt_generator import PromptGenerator
from pr_agent.llm.litellm import LiteLLMModel, clip_text
from pr_agent.prompting.prompts import pr_review_prompt_system, pr_review_prompt_user
from pr_agent.types import FilePatchInfo

class TaskInference(ABC):
    def initialize_task(self, task):
        self.prompt_genetator: Optional[PromptGenerator] = None
        self.valid_values = None

    @abstractmethod
    def transform(self, task: PRTask) -> PRTask:
        pass

class PRReviewTaskInference(TaskInference):
    def __init__(self, llm: LiteLLMModel):
        self.llm = llm

    def transform(self, task: PRTask) -> PRTask:
        prompt = pr_review_prompt_system()
        init_tokens = self.llm.count_tokens(prompt)
        pr_diffs = "\n\n".join([
            f"## File: {diff.filename}\n"
            f"{diff.patch}"
            for diff in task.diff_files
            if diff
        ])
        pr_diffs = clip_text(pr_diffs, self.llm.model, self.llm.model_max_input_tokens - init_tokens)
        text = pr_review_prompt_user(pr_diffs)
        response = self.llm.query(
            messages=[
                {
                    "role": "system",
                    "content": pr_review_prompt_system()
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        )
        
        return response
