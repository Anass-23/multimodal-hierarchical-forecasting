from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ClickstreamData(BaseModel):
    """
    User interaction/activity log entry.

    Captures detailed information about student actions within the system specifically (normally related to a course).
    """

    id: int = Field(..., description="Unique event identifier")
    eventname: str = Field(..., description="Type of event that occurred")
    timestamp: datetime = Field(..., description="Event datetime")
    action: Optional[str] = Field(None, description="Action type performed")
    target: Optional[str] = Field(None, description="Target resource of the action")
    ip: Optional[str] = Field(None, description="IP address of the user")
