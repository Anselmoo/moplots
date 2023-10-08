"""Command line interface for Molecular Orbitals (MOs) plot.

Currently, only ORCA is supported for the generation of MOs of the following
types:

    - .gbw
    - .qro
    - .uno
    - .uco

The MOs are plotted using the ORCA_PLOT program, which is part of the ORCA package.
"""

import argparse
import json
import shutil
import subprocess
import tempfile
from abc import ABC, abstractmethod
from argparse import Namespace, _ArgumentGroup
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from tempfile import _TemporaryFileWrapper
from typing import List, Tuple, Type, TypedDict, Union

from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    TaskID,
    TextColumn,
)
from rich.table import Table
from rich_argparse import ArgumentDefaultsRichHelpFormatter, RichHelpFormatter

from moplots import __moplots__, __repo__, __version__

console = Console(force_terminal=True, color_system="auto")


class OutputType(Enum):
    """Enum class for storing the output types."""

    BINARY = 5
    ASCII = 6
    CUBE = 7


@dataclass(frozen=False)
class Config:
    """Class for storing the configuration of moplots."""

    types_of_orbitals: Tuple[str] = (".gbw", ".qro", ".uno", ".uco")
    types_of_output: Tuple[str] = tuple(OutputType.__members__)
    config_file: Path = Path.home() / ".config" / "moplots" / "config.json"
    orca_plot_path: Union[str, None] = None

    def __post_init__(self) -> None:
        """Initialize the orca_plot_path attribute lazily."""
        if self.orca_plot_path is None:
            self.orca_plot_path = shutil.which("orca_plot")


config = Config()


def check_file_suffix(fname: str) -> Path:
    """Check if the file suffix is valid.

    Args:
        fname (str): File name with suffix.

    Raises:
        argparse.ArgumentTypeError: If the file suffix is not valid.

    Returns:
        Path: Path object of the file.
    """
    suffix = Path(fname).suffix
    if suffix not in config.types_of_orbitals:
        msg = "Invalid file suffix"
        raise argparse.ArgumentTypeError(msg)
    return Path(fname)


def validate_args(args: Namespace) -> None:
    """Validate the arguments."""
    if args.mo0 is None or args.mo1 is None:
        msg = "Both mo0 and mo1 arguments are required."
        raise ValueError(msg)

    if args.mo0 < 0 or args.mo1 < 0:
        msg = "Both mo0 and mo1 arguments must be positive."
        raise ValueError(msg)

    if config.orca_plot_path is None:
        msg = "orca_plot not found. Please make sure that 'orca_plot' is installed."
        raise FileNotFoundError(msg)


def epilog() -> str:
    """Returns a string containing information about how to use moplots to plot.

    Returns:
        str: A string containing information about how to use moplots to plot a series
            of molecular orbitals.
    """
    types_of_orbitals: str = ", ".join(f"'*{ext}'" for ext in config.types_of_orbitals)
    return (
        f"For plotting of series of molecular orbitals,"
        f" coming from [i]{types_of_orbitals}[/i],"
        f" {__moplots__} can be used to automatically generate these orbital plots. "
        f" For more information, please visit"
        f" For more information, please visit <[u]{__repo__}[/u]>."
    )


class SpinColor(TypedDict):
    """Type for storing the color of the spin."""

    alpha: str
    beta: str
    both: str


class MORangeColor(TypedDict):
    """Type for storing the color of the MO range."""

    start: str
    end: str
    type_: str


class ProgressColor(TypedDict):
    """Type for storing the color of the progress."""

    bar: str
    text: str
    percentage: str


class InfoColor(TypedDict):
    """Type for storing the color of the info."""

    title: str
    text: str


class TableColor(TypedDict):
    """Type for storing the color of the table."""

    title: str
    text: str
    left_column: str


class ArgsStyle(TypedDict):
    """Class for storing the style of the arguments."""

    argparse_args: str
    argparse_groups: str
    argparse_metavar: str
    argparse_help: str
    argparse_prog: str
    argparse_syntax: str
    argparse_text: str


class ColorTypedScheme(TypedDict):
    """Type for storing the color scheme."""

    background: str
    current_line: str
    foreground: str
    comment: str
    cyan: str
    green: str
    orange: str
    pink: str
    purple: str
    red: str
    yellow: str


class ColorScheme(ABC):
    """Abstract base class for color schemes."""

    @abstractmethod
    def get_colors(self) -> ColorTypedScheme:
        """Return a dictionary of color names and their values."""


class DraculaScheme(ColorScheme):
    """Concrete class for the Dracula color scheme."""

    def get_colors(self) -> ColorTypedScheme:
        """Return a ColorTypedScheme of color names and their values."""
        return ColorTypedScheme(
            background="#282a36",
            current_line="#44475a",
            foreground="#f8f8f2",
            comment="#6272a4",
            cyan="#8be9fd",
            green="#50fa7b",
            orange="#ffb86c",
            pink="#ff79c6",
            purple="#bd93f9",
            red="#ff5555",
            yellow="#f1fa8c",
        )


class MonokaiScheme(ColorScheme):
    """Concrete class for the Monokai color scheme."""

    def get_colors(self) -> ColorTypedScheme:
        """Return a ColorTypedScheme of color names and their values."""
        return ColorTypedScheme(
            background="#272822",
            current_line="#3e3d32",
            foreground="#f8f8f2",
            comment="#75715e",
            cyan="#66d9ef",
            green="#a6e22e",
            orange="#fd971f",
            pink="#f92672",
            purple="#ae81ff",
            red="#e74c3c",
            yellow="#e6db74",
        )


class MaterialScheme(ColorScheme):
    """Concrete class for the Material color scheme."""

    def get_colors(self) -> ColorTypedScheme:
        """Return a ColorTypedScheme of color names and their values."""
        return ColorTypedScheme(
            background="#263238",
            current_line="#37474f",
            foreground="#eceff1",
            comment="#546e7a",
            cyan="#80cbc4",
            green="#c3e88d",
            orange="#ffcb6b",
            pink="#f48fb1",
            purple="#b48ead",
            red="#ff5370",
            yellow="#ffcb6b",
        )


class NordScheme(ColorScheme):
    """Concrete class for the Nord color scheme."""

    def get_colors(self) -> ColorTypedScheme:
        """Return a ColorTypedScheme of color names and their values."""
        return ColorTypedScheme(
            background="#2e3440",
            current_line="#3b4252",
            foreground="#d8dee9",
            comment="#4c566a",
            cyan="#88c0d0",
            green="#a3be8c",
            orange="#d08770",
            pink="#b48ead",
            purple="#81a1c1",
            red="#bf616a",
            yellow="#ebcb8b",
        )


class OneDarkScheme(ColorScheme):
    """Concrete class for the One Dark color scheme."""

    def get_colors(self) -> ColorTypedScheme:
        """Return a ColorTypedScheme of color names and their values."""
        return ColorTypedScheme(
            background="#21252B",
            current_line="#282C34",
            foreground="#ABB2BF",
            comment="#5C6370",
            cyan="#56B6C2",
            green="#98C379",
            orange="#D19A66",
            pink="#C678DD",
            purple="#C678DD",
            red="#E06C75",
            yellow="#E5C07B",
        )


class SolarizedDarkScheme(ColorScheme):
    """Concrete class for the Solarized Dark color scheme."""

    def get_colors(self) -> ColorTypedScheme:
        """Return a ColorTypedScheme of color names and their values."""
        return ColorTypedScheme(
            background="#002b36",
            current_line="#073642",
            foreground="#839496",
            comment="#586e75",
            cyan="#2aa198",
            green="#859900",
            orange="#cb4b16",
            pink="#d33682",
            purple="#6c71c4",
            red="#dc322f",
            yellow="#b58900",
        )


class AddMoreColorSchemes(ColorScheme):
    """Concrete class for the Solarized Dark color scheme."""

    def get_colors(self) -> ColorTypedScheme:
        """Return a ColorTypedScheme of color names and their values."""
        raise NotImplementedError


class SchemeDict(TypedDict):
    """Type for storing the color schemes."""

    dracula: Type[DraculaScheme]
    monokai: Type[MonokaiScheme]
    material: Type[MaterialScheme]
    nord: Type[NordScheme]
    one_dark: Type[OneDarkScheme]
    solarized_dark: Type[SolarizedDarkScheme]


def raise_scheme_error(scheme_name: str) -> None:
    """Raise a ValueError with the given message."""
    if scheme_name not in SchemeDict.__annotations__:
        msg: str = (
            "Invalid scheme name. Options are:"
            f"[u][i] {', '.join(SchemeDict.__annotations__)}[/u][/i]"
        )
        raise ValueError(msg)


class ColorSchemeFactory:
    """Factory class for creating color schemes."""

    @staticmethod
    def create_color_scheme(scheme_name: str) -> ColorScheme:
        """Create a color scheme based on the given name."""
        scheme_dict: SchemeDict = {
            "dracula": DraculaScheme,
            "monokai": MonokaiScheme,
            "material": MaterialScheme,
            "nord": NordScheme,
            "one_dark": OneDarkScheme,
            "solarized_dark": SolarizedDarkScheme,
        }
        raise_scheme_error(scheme_name)
        return scheme_dict[scheme_name]()


class SetTheme:
    """Class for storing the color themes."""

    def __init__(self: "SetTheme") -> None:
        """Initialize the class."""
        self.theme_name = self.load_theme_name()
        self.color_scheme: ColorScheme = ColorSchemeFactory.create_color_scheme(
            self.theme_name,
        )

    def load_theme_name(self: "SetTheme") -> str:
        """Load the theme name from the config file."""
        if config.config_file.exists():
            with Path.open(config.config_file, "r", encoding="utf-8") as f:
                theme = json.load(f)["theme"]
        else:
            theme = {"theme": "dracula"}
            # Create the config file with complete path
            config.config_file.parent.mkdir(parents=True, exist_ok=True)
            # Write the default theme
            with Path.open(config.config_file, "w", encoding="utf-8") as f:
                json.dump(theme, f)
        return theme

    def set_theme(self: "SetTheme", theme_name: str) -> None:
        """Set to a new theme and save to the config file."""
        raise_scheme_error(theme_name)
        self.color_scheme = ColorSchemeFactory.create_color_scheme(theme_name)

        with Path.open(config.config_file, "w", encoding="utf-8") as f:
            json.dump({"theme": theme_name}, f)

    @property
    def get_arparse_style(self) -> ArgsStyle:
        """Get the argparse style."""
        styles: ArgsStyle = ArgsStyle(
            argparse_args=f"bold {self.color_scheme.get_colors()['pink']}",
            argparse_groups=f"bold {self.color_scheme.get_colors()['purple']}",
            argparse_metavar=f"italic {self.color_scheme.get_colors()['yellow']}",
            argparse_help=f"{self.color_scheme.get_colors()['foreground']}",
            argparse_prog=f"bold {self.color_scheme.get_colors()['orange']}",
            argparse_syntax=f"{self.color_scheme.get_colors()['green']}",
            argparse_text=f"{self.color_scheme.get_colors()['cyan']}",
        )
        # Replace _ with . in the keys
        return {k.replace("_", "."): v for k, v in styles.items()}

    @property
    def get_spin_style(self) -> SpinColor:
        """Get the spin style."""
        return SpinColor(
            alpha=f"italic {self.color_scheme.get_colors()['green']}",
            beta=f"italic {self.color_scheme.get_colors()['red']}",
            both=f"italic {self.color_scheme.get_colors()['cyan']}",
        )

    @property
    def get_mo_range_style(self) -> MORangeColor:
        """Get the MO range style."""
        return MORangeColor(
            start=f"bold underline {self.color_scheme.get_colors()['yellow']}",
            end=f"bold underline {self.color_scheme.get_colors()['yellow']}",
            type_=f"bold {self.color_scheme.get_colors()['cyan']}",
        )

    @property
    def get_progress_style(self) -> ProgressColor:
        """Get the progress style."""
        return ProgressColor(
            bar=f"italic {self.color_scheme.get_colors()['red']}",
            bar_complete=f"italic {self.color_scheme.get_colors()['orange']}",
            bar_finished=f"italic {self.color_scheme.get_colors()['green']}",
            text=f"bold {self.color_scheme.get_colors()['pink']}",
            percentage=f"bold {self.color_scheme.get_colors()['yellow']}",
        )

    @property
    def get_info_style(self) -> InfoColor:
        """Get the info style."""
        return InfoColor(
            title=f"bold {self.color_scheme.get_colors()['purple']}",
            text=f"italic {self.color_scheme.get_colors()['pink']}",
        )

    @property
    def get_table_style(self) -> TableColor:
        """Get the table style."""
        return TableColor(
            title=f"bold {self.color_scheme.get_colors()['foreground']}",
            header=f"bold {self.color_scheme.get_colors()['pink']}",
            left_column=f"bold {self.color_scheme.get_colors()['purple']}",
        )


class Command(ABC):
    """Abstract base class for commands."""

    @abstractmethod
    def execute(self) -> None:
        """Execute the command."""


class GenerateMOPlotsCommand(Command):
    """Command to generate MO plots."""

    def __init__(
        self,
        args: argparse.Namespace,
        spin: str,
        bar_style: ProgressColor,
        info_style: InfoColor,
    ) -> None:
        """Initialize the class.

        Args:
            args (argparse.Namespace): Arguments passed to the command.
            spin (str): Spin of the MOs to plot.
            bar_style (ProgressColor): Style of the progress bar.
            info_style (InfoColor): Style of the info.
        """
        self.args: Namespace = args
        self.spin: str = spin
        self.bar_style: ProgressColor = bar_style
        self.info_style: InfoColor = info_style

    def execute(self) -> None:
        """Execute the command to generate MO plots."""
        mo_range = range(self.args.mo0, self.args.mo1 + 1)

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(
                style=self.bar_style["bar"],
                complete_style=self.bar_style["bar_complete"],
                finished_style=self.bar_style["bar_finished"],
                bar_width=None,
            ),
            TextColumn(
                "[progress.percentage]{task.percentage:>3.0f}%",
                style=self.bar_style["percentage"],
            ),
            expand=True,
        ) as progress:
            task1: TaskID = progress.add_task(
                f"[{self.info_style['text']}]Generating MO plots[/]",
                total=len(mo_range),
                start=True,
            )
            for i in mo_range:
                progress.update(task1, advance=1)
                if self.spin in ["alpha", "both"]:
                    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp:
                        self._write_spin(temp, i, "0\n1\n1\n")

                    filename = temp.name

                    subprocess.run(
                        f"{config.orca_plot_path} {self.args.infile[0].name }"
                        f" -i < {filename} > {filename}.log",
                        shell=True,  # noqa: S602
                        check=True,
                    )
                if self.spin in ["beta", "both"]:
                    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp:
                        self._write_spin(temp, i, "1\n1\n1\n")
                    filename: str = temp.name
                    subprocess.run(
                        f"{config.orca_plot_path} {self.args.infile[0].name }"
                        f" -i < {filename} > {filename}.log",
                        shell=True,  # noqa: S602
                        check=True,
                    )

    def _write_spin(
        self,
        temp: _TemporaryFileWrapper,
        mo_i: int,
        spin: str,
    ) -> None:
        """Write the spin to the temporary file."""
        temp.write(f"4\n{self.args.grid}\n2\n{mo_i}\n3\n")
        temp.write(spin)
        temp.write(f"5\n{OutputType[self.args.output].value}\n10\n11\n")


class CommandInvoker:
    """Class to invoke commands."""

    def __init__(self) -> None:
        """Initialize the class."""
        self._commands: List[Command] = []

    def add_command(self, command: Command) -> None:
        """Add a command to the invoker."""
        self._commands.append(command)

    def execute_commands(self) -> None:
        """Execute all commands in the invoker."""
        for command in self._commands:
            command.execute()


def main() -> None:
    """Main function for the command line interface."""
    RichHelpFormatter.styles = SetTheme().get_arparse_style

    parser = argparse.ArgumentParser(
        prog=__moplots__,
        usage=f"{__moplots__} [options] <infile>",
        description="Molecular Orbital Plots as Batch Series for ORCA",
        epilog=epilog(),
        formatter_class=ArgumentDefaultsRichHelpFormatter,
    )

    parser.add_argument(
        "infile",
        type=check_file_suffix,
        nargs=1,
        help="Read the orbitals file of ORCA",
    )

    group_mos: _ArgumentGroup = parser.add_argument_group(
        title=" Arguments",
        description=f"These arguments are essential to run {__moplots__}",
    )
    group_mos.add_argument(
        "-m0",
        "--mo0",
        dest="mo0",
        type=int,
        help="First [b]M[/b]olecular [b]O[/b]rbital  to plot of the series",
    )
    group_mos.add_argument(
        "-m1",
        "--mo1",
        dest="mo1",
        type=int,
        help="Last [b]M[/b]olecular[b] O[/b]rbital to plot of the series",
    )

    group_settings: _ArgumentGroup = parser.add_argument_group(
        title=" Settings",
        description="These settings are optional.",
    )

    group_settings.add_argument(
        "-c",
        "--color",
        type=lambda s: s.lower(),
        default="dracula",
        dest="color",
        choices=SchemeDict.__annotations__,
        help=f"Select color scheme for the terminal printout."
        f" Options are [i][u]'{', '.join(SchemeDict.__annotations__)}'[/i][/u] and"
        f" updates the '{config.config_file}' file.",
    )

    group_settings.add_argument(
        "-o",
        "--output",
        type=lambda s: s.upper(),
        default="BINARY",
        dest="output",
        choices=config.types_of_output,
        help="Select output type. Options are"
        f" '[i][u]{ ', '.join(config.types_of_output)}[/i][/u]'.",
    )

    group_settings.add_argument(
        "-g",
        "--grid",
        type=int,
        default=80,
        dest="grid",
        help="Select the grid size for the plot.",
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"[argparse.prog]%(prog)s[/] [i] v{__version__}",
    )

    parser.add_argument(
        "-s",
        "--spin",
        type=lambda s: s.lower(),
        default="alpha",
        dest="spin",
        choices=["alpha", "beta", "both"],
        help="Select spin of MOs to plot. Options are 'alpha', 'beta', 'both'.",
    )

    args: Namespace = parser.parse_args()

    validate_args(args)

    if args.color != SetTheme().theme_name:
        SetTheme().set_theme(args.color)

    spin_color: SpinColor = SetTheme().get_spin_style
    mo_range_color: MORangeColor = SetTheme().get_mo_range_style
    info_style: InfoColor = SetTheme().get_info_style
    table_style: TableColor = SetTheme().get_table_style
    bar_style: ProgressColor = SetTheme().get_progress_style

    title_text: str = f"[{info_style['title']}]moplots v{__version__}[/]"
    table = Table(title=f"[{table_style['title']}]Active Selection[/]", expand=True)
    table.add_column(f"[{table_style['header']}]Parameter[/]")
    table.add_column(f"[{table_style['header']}]Value[/]")

    table.add_row(
        f"[{table_style['left_column']}]Input[/]",
        f"[{mo_range_color['type_']}]{args.infile[0].stem}[/]"
        f" [{info_style['text']}]of type[/]"
        f" [{mo_range_color['type_']}]{args.infile[0].suffix}[/]",
    )
    table.add_row(
        f"[{table_style['left_column']}]MO Total[/]",
        f"[{mo_range_color['type_']}]{args.mo1 - args.mo0 + 1}[/]",
    )
    table.add_row(
        f"[{table_style['left_column']}]MO Range[/]",
        f"[{mo_range_color['type_']}]{args.mo0}[/]"
        f" [{info_style['text']}]to[/]"
        f" [{mo_range_color['type_']}]{args.mo1}[/]",
    )
    table.add_row(
        f"[{table_style['left_column']}]Spin Info[/]",
        f"[{spin_color[args.spin]}]{args.spin}[/]",
    )
    table.add_row(
        f"[{table_style['left_column']}]Output[/]",
        f"[{mo_range_color['type_']}]{args.output}[/]",
    )

    outer_panel = Panel(table, title=title_text, expand=True)

    print(outer_panel)

    command_invoker = CommandInvoker()
    command_invoker.add_command(
        GenerateMOPlotsCommand(args, args.spin, bar_style, info_style),
    )
    command_invoker.execute_commands()
