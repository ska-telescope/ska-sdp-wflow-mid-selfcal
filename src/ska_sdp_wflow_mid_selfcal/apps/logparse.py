from __future__ import annotations

import argparse
import functools
import math
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments into a convenient object.
    """
    parser = argparse.ArgumentParser(
        description="Parse pipeline logs into a performance report",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "logfiles",
        nargs="+",
        type=os.path.realpath,
        help="Log files to parse.",
    )
    return parser.parse_args()


@dataclass
class LogEntry:
    level: str
    time: datetime
    program: Optional[str]
    message: str


def _entries_time_span_seconds(entries: list[LogEntry]) -> float:
    if not entries:
        return 0.0
    return (entries[-1].time - entries[0].time).total_seconds()


@dataclass
class LogEntryBlock:
    program: str
    entries: list[LogEntry]
    duration: float = field(init=False)

    def __post_init__(self):
        self.duration = _entries_time_span_seconds(self.entries)


REGEX = re.compile(r"\[(.*?) - (.*?) - (.*?)\](.*)")
""" Regular expression to split a log line """


PROGRAM_NAMES = {"DP3", "wsclean"}


def _get_program(logger_name: str) -> Optional[str]:
    groups = logger_name.split(".")
    if not len(groups) > 1:
        return None
    program = groups[1]
    if program not in PROGRAM_NAMES:
        return None
    return program


def parse_line(line: str) -> Optional[LogEntry]:
    """Parse a log line into a convenient object. Return `None` if the line
    could not be parsed."""
    match = re.match(REGEX, line)
    if not match:
        return None
    level, time_str, logger_name, message = match.groups()
    time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S,%f")
    program = _get_program(logger_name)
    message = message.strip()
    return LogEntry(level, time, program, message)


def parse_lines_into_entries(lines: list[str]) -> list[LogEntry]:
    """
    Parse log lines into a list of entries. Discard lines that have no logging
    header, or whose message is empty.
    """
    entries = [parse_line(line) for line in lines]
    entries = [
        entry
        for entry in entries
        if entry and entry.message and not entry.message.isspace()
    ]
    return entries


def split_log_entry_blocks(log_entries: list[LogEntry]) -> list[LogEntryBlock]:
    """
    Split a list of log entries into sequential blocks where each block has
    been produced by either DP3 or wsclean. Blocks are contiguous sub-lists
    of entries where the program name remains the same.

    NOTE: this function will NOT return incomplete blocks, e.g. if the program
    did not successfully finish.
    """
    regex_start = re.compile(r"Running (DP3|wsclean)")
    regex_end = re.compile(r"(DP3|wsclean) finished in.*")

    current_program = None
    current_entries: list[LogEntry] = []
    output_blocks: list[LogEntryBlock] = []

    def _parse_block_start_program(entry: LogEntry) -> Optional[str]:
        match = regex_start.match(entry.message)
        return match[1] if match else None

    def _is_block_end(entry: LogEntry) -> bool:
        return regex_end.match(entry.message)

    def _should_accumulate() -> bool:
        return current_program is not None

    for entry in log_entries:
        if _is_block_end(entry):
            current_entries.append(entry)
            block = LogEntryBlock(current_program, current_entries)
            output_blocks.append(block)
            current_entries = []
            current_program = None

        if prog := _parse_block_start_program(entry):
            current_program = prog

        if _should_accumulate():
            current_entries.append(entry)

    return output_blocks


def parse_pipeline_arguments(log_entries: list[LogEntry]) -> dict[str, Any]:
    """
    Parse the pipeline arguments that are relevant for benchmarking.
    """

    def parse_npix(msg: str) -> Optional[int]:
        match = re.match(r"size: \[(\d+), (\d+)\]", msg)
        if not match:
            return None
        width, height = [int(g) for g in match.groups()]
        return round(math.sqrt(width * height))

    def parse_input_ms(msg: str) -> Optional[str]:
        match = re.match(r"input_ms: (.*)", msg)
        return match[1] if match else None

    def parse_num_nodes(msg: str) -> Optional[int]:
        match = re.match(r"SLURM allocated nodes: (\d+)", msg)
        return int(match[1]) if match else None

    parsers = {
        "nodes": parse_num_nodes,
        "npix": parse_npix,
        "input_ms": parse_input_ms,
    }

    result = {
        "nodes": 1,
        "npix": None,
        "input_ms": None,
    }

    for entry in log_entries:
        if entry.message.startswith("Merging input measurement sets into one"):
            break

        for arg, parser in parsers.items():
            value = parser(entry.message)
            if value is not None:
                result[arg] = value

    return result


def wsclean_runtime_breakdown(entries: list[LogEntry]) -> dict[str, float]:
    """
    Given a list of log entries corresponding to a completed run of
    WSClean, return a dictionary containing a run time breakdown in seconds.
    """
    regex_message = re.compile(
        r"Inversion: (.*?), prediction: (.*?), deconvolution: (.*)"
    )
    regex_duration = re.compile(r"(\d+):(\d{2}):(\d{2})\.(\d{6})")

    def _parse_wsclean_duration_string(s: str) -> float:
        hours, minutes, seconds, microseconds = [
            int(group) for group in regex_duration.match(s).groups()
        ]
        return 3600.0 * hours + 60.0 * minutes + seconds + microseconds / 1.0e6

    for entry in entries:
        message_match = regex_message.match(entry.message)
        if message_match:
            break

    inversion, prediction, deconvolution = [
        _parse_wsclean_duration_string(group)
        for group in message_match.groups()
    ]

    total = _entries_time_span_seconds(entries)
    unaccounted = total - (inversion + prediction + deconvolution)
    return {
        "wsclean_inversion": inversion,
        "wsclean_prediction": prediction,
        "wsclean_deconvolution": deconvolution,
        "wsclean_unaccounted": unaccounted,
        "wsclean_total": total,
    }


def dp3_gaincal_runtime_breakdown(entries: list[LogEntry]) -> dict[str, float]:
    """
    Given a list of log entries corresponding to a completed run of DP3
    gaincal, return a dictionary containing a run time breakdown inseconds.
    """

    def _parse_dp3_time_string(s: str) -> float:
        # e.g. "4242 ms" or "12 s"
        duration_str, unit = s.strip().split()
        scale = 1.0e-3 if unit == "ms" else 1.0
        return float(duration_str) * scale

    def _parse_step_runtime(msg: str, step_name: str) -> Optional[float]:
        match = re.match(rf".*?\((.*?)\) {step_name}", msg)
        return _parse_dp3_time_string(match[1]) if match else None

    step_names = ["MSReader", "GainCal", "MSUpdater"]
    result = {step: None for step in step_names}

    for entry in entries:
        for step_name in step_names:
            runtime = _parse_step_runtime(entry.message, step_name)
            if runtime is not None:
                result[step_name] = runtime

    # NOTE: The reported time breakdown sometimes adds up to more than the
    # total runtime, probably because the reported run times of some steps are
    # rounded up.
    total = _entries_time_span_seconds(entries)
    result["total"] = total
    return {f"dp3_{key}": value for key, value in result.items()}


def _dictionary_sum(dicts: list[dict[str, float]]) -> dict[str, float]:
    if not dicts:
        return {}
    keys = dicts[0].keys()
    return {key: sum(d[key] for d in dicts) for key in keys}


def _pipeline_outcome(entries: list[LogEntry]) -> str:
    if any(entry.message == "Pipeline run: SUCCESS" for entry in entries):
        return "success"
    if any(entry.message == "Pipeline run: FAIL" for entry in entries):
        return "fail"
    return "unknown"


def parse_logfile(fname: str) -> dict[str, Any]:
    fname = os.path.realpath(fname)
    with open(fname, "r") as fobj:
        lines = fobj.read().strip().split("\n")

    entries = parse_lines_into_entries(lines)

    outcome = _pipeline_outcome(entries)
    total_runtime_seconds = _entries_time_span_seconds(entries)
    pipeline_args = parse_pipeline_arguments(entries)

    blocks = split_log_entry_blocks(entries)

    # Remove first DP3 block. It is a merge step that we don't want to include.
    for block in blocks:
        if block.program == "DP3":
            blocks.remove(block)
            break

    dp3_breakdowns = []
    wsclean_breakdowns = []

    for block in blocks:
        if block.program == "wsclean":
            wsclean_breakdowns.append(
                (wsclean_runtime_breakdown(block.entries))
            )
        if block.program == "DP3":
            dp3_breakdowns.append(dp3_gaincal_runtime_breakdown(block.entries))

    dp3_summary = _dictionary_sum(dp3_breakdowns)
    wsclean_summary = _dictionary_sum(wsclean_breakdowns)
    global_summary = {}
    global_summary.update(
        {
            "filename": fname,
            "pipeline_total": total_runtime_seconds,
            "outcome": outcome,
        }
    )
    global_summary.update(pipeline_args)
    global_summary.update(dp3_summary)
    global_summary.update(wsclean_summary)
    return global_summary


def main():
    """
    Entry point for the logs parsing app.
    """
    args = parse_args()
    summaries: list[dict[str, Any]] = []
    for fname in args.logfiles:
        summaries.append(parse_logfile(fname))

    def list_to_csv_row(items: list) -> str:
        return ",".join([f'"{val}"' for val in items])

    keys = functools.reduce(set.union, (s.keys() for s in summaries), set())
    keys = sorted(list(keys))

    csv_header = list_to_csv_row(keys)
    print(csv_header)

    for summary in summaries:
        row = list_to_csv_row([summary.get(k, "") for k in keys])
        print(row)


if __name__ == "__main__":
    main()
