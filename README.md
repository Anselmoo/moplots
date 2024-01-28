# MOPlots

[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/moplots?logo=pypi&logoColor=yellow)](https://pypi.org/project/moplots/)

> [!INFO]
> MOPlots is a command line (CMD) tool, which allows you to use
> [`orca_plot`](https://www.orcasoftware.de/tutorials_orca/react/FUKUI.html#generating-a-cube-file) in automated way
> to generate a series of plots for MOs for both `alpha` and `beta` spin channels.

## Installation

Requires Python 3.7 or higher.

```bash
pip install moplots
```

and `orca_plot` from [ORCA](https://www.orcasoftware.de/tutorials_orca/) has to be in your `PATH`.

## Usage

```bash
moplots --help
```

### Example

```bash
moplots  test.gbw -s both -m0 1 -m1 18 -o cube
```

> By executing the above command, you will get a series of cube files for
> MOs from 1 to 18 for both `alpha` and `beta` spin channels.

## License

The code is licensed under the [MIT](LICENSE).

## Further reading

[ORCA tutorials](https://www.orcasoftware.de/tutorials_orca/index.html#)
