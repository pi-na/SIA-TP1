from __future__ import annotations

import threading
import time

from src.engine.search import search
from src.ui.solver.comparison_table import MethodResult, mark_optimals
from src.ui.solver.method_definitions import MethodSpec


class SolverWorker:
    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._initial_state = None
        self._methods: list[MethodSpec] = []
        self._results: list[MethodResult] = []
        self._progress: list[str] = []
        self._lock = threading.Lock()
        self._done = False
        self._cancelled = False

    def start(self, initial_state, methods: list[MethodSpec]) -> None:
        self._initial_state = initial_state
        self._methods = list(methods)
        self._results = []
        self._progress = ["pending"] * len(methods)
        self._done = False
        self._cancelled = False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def cancel(self) -> None:
        self._cancelled = True

    def is_done(self) -> bool:
        with self._lock:
            return self._done

    def get_progress(self) -> list[tuple[MethodSpec, str]]:
        with self._lock:
            return list(zip(self._methods, list(self._progress)))

    def get_results(self) -> list[MethodResult] | None:
        with self._lock:
            if not self._done:
                return None
            return list(self._results)

    def _run(self) -> None:
        for i, method in enumerate(self._methods):
            if self._cancelled:
                break
            with self._lock:
                self._progress[i] = "running"

            start_t = time.perf_counter()
            search_result = search(
                self._initial_state,
                method=method.algorithm,
                heuristic=method.heuristic,
                base_heuristic=method.base_heuristic,
            )
            elapsed = time.perf_counter() - start_t

            result = MethodResult(
                spec=method,
                result=search_result["result"],
                cost=search_result.get("cost"),
                time_seconds=elapsed,
                nodes_expanded=search_result["nodes_expanded"],
                frontier_count=search_result["frontier_count"],
                path=search_result.get("path", []),
            )

            with self._lock:
                self._results.append(result)
                self._progress[i] = "done"

        if not self._cancelled:
            mark_optimals(self._results)
        with self._lock:
            self._done = True
