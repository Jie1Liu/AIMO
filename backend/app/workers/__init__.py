from __future__ import annotations
from typing import Optional
"""SQS worker entry points.

The MVP processes jobs synchronously for a demo-friendly local loop. These modules
keep the production worker boundary explicit for AWS SQS integration.
"""
