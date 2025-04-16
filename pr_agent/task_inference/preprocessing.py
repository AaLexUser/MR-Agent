from pr_agent.task_inference.base import TaskInference
from pr_agent.task import PRTask
from collections import Counter, defaultdict
import os


class SortByLanguageTask(TaskInference):
    def transform(self, task: PRTask) -> PRTask:
        if task.diff_files:
            # Extract extensions and count them
            ext_counter = Counter()
            ext_to_files = defaultdict(list)
            for file in task.diff_files:
                _, ext = os.path.splitext(file.filename)
                ext = ext.lower()
                ext_counter[ext] += 1
                ext_to_files[ext].append(file)
            # Sort extensions by count (descending)
            sorted_exts = [ext for ext, _ in ext_counter.most_common()]
            # Rebuild diff_files sorted by most common extension
            sorted_files = []
            for ext in sorted_exts:
                sorted_files.extend(ext_to_files[ext])
            task.diff_files = sorted_files
        return task
