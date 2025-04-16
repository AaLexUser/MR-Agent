from datetime import datetime
from typing import Dict, Any, Optional, List
from pr_agent.types import FilePatchInfo
        
class PRTask:
    def __init__(self, pr_url: str, author: str):
        self._pr_url = pr_url
        self._author = author
        self._metadata: Dict[str, Any] = {
            "closed_at": None,
            "diff_files": None,
        }  
    
    @property
    def closed_at(self) -> Optional[datetime]:
        return self._metadata["closed_at"]

    @closed_at.setter
    def closed_at(self, value: datetime):
        self._metadata["closed_at"] = value
    
    @property
    def diff_files(self) -> List[FilePatchInfo]:
        return self._metadata["diff_files"] or []

    @diff_files.setter
    def diff_files(self, value: List[FilePatchInfo]):
        self._metadata["diff_files"] = value
        
        
