"""
LangSmith tracing wrapper.
JD point 2: trace logging, replayability, step-level observability.
Gracefully no-ops if LANGCHAIN_API_KEY not set.
"""
import os
import time
from contextlib import contextmanager
from typing import Dict, Any
from config import cfg


class _NoOpTracer:
    def log_step(self, name: str, data: Dict = {}):
        pass
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass


class _LangSmithTracer:
    def __init__(self, run_name: str, inputs: Dict):
        self.run_name = run_name
        self.inputs = inputs
        self.steps = []
        self.start = time.time()
        self._run = None

    def log_step(self, name: str, data: Dict = {}):
        self.steps.append({"step": name, "t": round(time.time() - self.start, 3), **data})

    def __enter__(self):
        try:
            from langsmith import Client
            self._ls_client = Client()
            self._run = self._ls_client.create_run(
                name=self.run_name,
                run_type="chain",
                inputs=self.inputs,
                project_name=cfg.LANGCHAIN_PROJECT,
            )
        except Exception as e:
            print(f"[LangSmith] trace start failed: {e}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if self._run:
                self._ls_client.update_run(
                    self._run.id,
                    outputs={"steps": self.steps},
                    end_time=time.time(),
                    error=str(exc_val) if exc_val else None,
                )
        except Exception as e:
            print(f"[LangSmith] trace end failed: {e}")


@contextmanager
def trace_run(name: str, inputs: Dict = {}):
    """Context manager that traces a named run to LangSmith."""
    if cfg.LANGCHAIN_TRACING_V2 and cfg.LANGCHAIN_API_KEY:
        os.environ["LANGCHAIN_API_KEY"] = cfg.LANGCHAIN_API_KEY
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = cfg.LANGCHAIN_PROJECT
        tracer = _LangSmithTracer(name, inputs)
    else:
        tracer = _NoOpTracer()

    with tracer as t:
        yield t
