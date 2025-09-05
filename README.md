# fm24tool

Simple Football Manager 2024 squad formation analyser.

Given an exported squad list as an HTML table, the tool evaluates a set of
common formations and scores them on a 0–100 scale based on each player's
attribute rating.  All formation scores are printed so you can compare how the
squad fits different shapes, with the best formation highlighted at the end.

The package includes a ``__main__`` entrypoint so it can be executed with
``python -m fm24_tool``. A broad selection of formations used in FM24, such as
``4-4-2`` or ``3-4-3``, are considered when determining the best fit.

## Usage

```
python -m fm24_tool path/to/squad.html
```
