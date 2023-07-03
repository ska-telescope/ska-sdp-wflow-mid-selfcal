from __future__ import annotations

import abc
import copy
from pathlib import Path
from typing import Optional, Sequence, Union

ScalarArg = Union[str, bool, int, float, Path]

Arg = Union[ScalarArg, Sequence[ScalarArg]]


def _render_scalar_arg(arg: ScalarArg) -> str:
    if isinstance(arg, Path):
        return arg.as_posix()

    if isinstance(arg, bool):
        return str(arg).lower()

    return str(arg)


def _dict_pretty_repr(mapping: dict, indent: int = 4) -> str:
    """
    Pretty print dictionary after sorting its keys.
    """
    tab = indent * " "
    lines = [f"{tab}{key!r}: {val!r}" for key, val in sorted(mapping.items())]
    lines = ["{"] + lines + [tab + "}"]
    return "\n".join(lines)


class Command(abc.ABC):
    """
    Base class for commands. Render using render_command() or
    render_command_with_modifiers().
    """

    def __init__(
        self,
        executable: str,
        positional_args: Sequence[ScalarArg],
        flags: Sequence[str],
        options: dict[str, Arg],
    ) -> None:
        """
        Create a new Command. How commands are actually rendered as a list of
        arguments is implemented in sub-classes.

        Args:
            executable: name of the binary executable for this command.
            positional_args: sequence of positional arguments for the command
            flags: sequence of boolean flags to specify with the command, for
                examples could be `--quiet` or `--verbose`.
            options: dictionary of optional arguments, where the keys are the
                prefix for the option, and the values the associated values.
        """
        self.executable = executable
        self.positional_args = list(positional_args)
        self.flags = set(flags)
        self.options = options

    @abc.abstractmethod
    def render_option(self, key: str, arg: Arg) -> list[str]:
        """
        Render an optional argument as a list of strings. How this is done
        is different for WSClean and DP3.
        """

    def __eq__(self, other: Command) -> bool:
        return (
            self.executable == other.executable
            and self.positional_args == other.positional_args
            and self.flags == other.flags
            and self.options == other.options
        )

    def __repr__(self) -> str:
        clsname = type(self).__name__
        options_repr = _dict_pretty_repr(self.options)
        lines = [
            f"{clsname}(",
            f"  executable={self.executable}",
            f"  positional_args={self.positional_args}",
            f"  flags={self.flags}",
            f"  options={options_repr}",
            ")",
        ]
        return "\n".join(lines)


class WSCleanCommand(Command):
    """
    Container for all the arguments in a WSClean command.
    """

    def __init__(
        self,
        measurement_sets: list[Path],
        *,
        flags: Sequence[str],
        options: dict[str, Arg],
    ) -> None:
        """
        Create a new WSCleanCommand.

        Args:
            measurement_sets: list of paths to the input measurement sets to
                process
            flags: list of flags to specify. Example flags are `-multiscale`,
                `-join-channels`.
            options: dictionary of additional options, keys are the associated
                prefix to the argument and values are the value of an argument
                in a native Python type.
        """
        super().__init__("wsclean", measurement_sets, flags, options)

    def render_option(self, key: str, arg: Arg) -> list[str]:
        """
        Appropriately render a WSClean option as a list of strings.
        """
        if isinstance(arg, (list, tuple)):
            rendered_arg = [_render_scalar_arg(item) for item in arg]
        else:
            rendered_arg = [_render_scalar_arg(arg)]
        return [key] + rendered_arg


class DP3Command(Command):
    """
    Container for all the arguments in a DP3 command.
    """

    def __init__(self, options: dict[str, Arg]) -> None:
        super().__init__("DP3", positional_args=[], flags=[], options=options)

    def render_option(self, key: str, arg: Arg) -> list[str]:
        """
        Appropriately render a DP3 option as a list of strings.
        """
        if isinstance(arg, (list, tuple)):
            csv = ",".join(_render_scalar_arg(item) for item in arg)
            rendered_arg = f"[{csv}]"
        else:
            rendered_arg = _render_scalar_arg(arg)
        return [f"{key}={rendered_arg}"]


class PrefixModifier(abc.ABC):
    """
    A command modifier that:
    1. Edits the command's arguments and options
    2. Prefixes the rendered command with additional arguments
    """

    @abc.abstractmethod
    def order(self) -> int:
        """
        An arbitrary number that defines the relative order in which multiple
        modifiers should be applied. Lower `order` commands are applied first.
        """

    @abc.abstractmethod
    def apply(self, cmd: Command) -> tuple[list[str], Command]:
        """
        Apply the modifier to the given command. Returns a tuple
        (prefixes, modified_command).
        """


class SingularityExec(PrefixModifier):
    """
    A command modifier that allows to render a command in such a way that it
    can be run inside a singularity container. When applied to a command, it
    does the following:
    1. Finds all the arguments of a command that are Path instances, and
    makes them absolute.
    2. Identifies the set of directories containing these path arguments
    3. Generates the right bind mount argument for each of these directories
    """

    def __init__(self, image_file: Path) -> None:
        """
        Create a new SingularityExec instance.

        Args:
            image_file: path to the singularity image file to use to run
                whatever commands on which this instance will operate.
        """
        self.image_file = image_file

    def order(self) -> int:
        return 1

    def apply(self, cmd: Command) -> tuple[list[str], Command]:
        modified_cmd = copy.deepcopy(cmd)
        bind_mount_pairs = set()

        def _replace_scalar_arg(arg: ScalarArg) -> ScalarArg:
            if not isinstance(arg, Path):
                return arg
            arg_absolute = arg.absolute()
            bind_mount_pairs.add(
                (str(arg_absolute.parent), "/mnt" + str(arg_absolute.parent))
            )
            return Path("/mnt" + str(arg_absolute))

        def _replace_arg(arg: Arg) -> Arg:
            if not isinstance(arg, (list, tuple)):
                return _replace_scalar_arg(arg)
            return [_replace_scalar_arg(item) for item in arg]

        # Replace all Path arguments with absolute versions
        modified_cmd.positional_args = list(
            map(_replace_arg, modified_cmd.positional_args)
        )
        modified_cmd.options = {
            key: _replace_arg(arg) for key, arg in modified_cmd.options.items()
        }

        # Generate prefixes
        bind_mount_args = []
        for (host_dir, target_dir) in sorted(bind_mount_pairs):
            bind_mount_args.extend(("--bind", f"{host_dir}:{target_dir}"))

        prefixes = [
            "singularity",
            "exec",
            *bind_mount_args,
            str(self.image_file),
        ]
        return prefixes, modified_cmd


class Mpirun(PrefixModifier):
    """
    A command modifier that allows to render a WSClean command so that it runs
    on multiple nodes via mpirun, distributing one frequency band to process
    to each node. Does the following:

    1. Adds/edits the following WSClean options:
    `-join-channels`
    `-channels-out N -deconvolution-channels 1 -fit-spectral-pol 1`
    where `N` is the number of nodes to use.

    2. Changes the executable from `wsclean` to `wsclean-mp`

    3. Prefixes the command with
    `mpirun -npernode 1 -np N`
    """

    def __init__(self, num_nodes: int) -> None:
        self.num_nodes = num_nodes

    def order(self) -> int:
        return 0

    def apply(self, cmd: Command) -> tuple[list[str], Command]:
        if not isinstance(cmd, WSCleanCommand) or self.num_nodes <= 1:
            return [], cmd

        modified_cmd = copy.deepcopy(cmd)
        modified_cmd.executable = "wsclean-mp"
        special_options = {
            "-channels-out": self.num_nodes,
            "-fit-spectral-pol": 1,
            "-deconvolution-channels": 1,
        }
        modified_cmd.options.update(special_options)
        modified_cmd.flags.add("-join-channels")

        prefixes = ["mpirun", "-np", str(self.num_nodes), "-npernode", str(1)]
        return prefixes, modified_cmd


def render_command(command: Command) -> list[str]:
    """
    Render the command as a list of strings. The rendering order is
    `<EXECUTABLE> <FLAGS> <OPTIONS> <POSITIONAL_ARGS>`.
    Flags, options and positional_args are alphabetically sorted.
    """
    args = [command.executable]
    args.extend(sorted(command.flags))

    options = command.options
    for key in sorted(options):
        val = options[key]
        args.extend(command.render_option(key, val))

    args.extend(_render_scalar_arg(val) for val in command.positional_args)
    return args


def render_command_with_modifiers(
    command: Command, modifiers: Optional[Sequence[PrefixModifier]] = None
) -> list[str]:
    """
    Render the command as a list of strings, applying any provided modifiers.
    The rendering order is
    `<EXECUTABLE> <FLAGS> <OPTIONS> <POSITIONAL_ARGS>`.
    Flags, options and positional_args are alphabetically sorted.
    """
    if not modifiers:
        return render_command(command)

    # Render recursively, applying the modifier with the lowest `order` first
    modifiers = sorted(modifiers, key=lambda m: m.order())
    mod = modifiers[0]
    prefixes, modified_command = mod.apply(command)
    return prefixes + render_command_with_modifiers(
        modified_command, modifiers[1:]
    )
