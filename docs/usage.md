# FM24 Tool Usage Guide

## Requirements
- Python 3.10 or later
- [pip](https://pip.pypa.io/)

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

## Running the Tool
1. Export your squad from Football Manager 2024 as an HTML table.
2. From this repository's root directory run:

```bash
python -m fm24_tool path/to/squad.html
```

Replace `path/to/squad.html` with the path to your exported file.  
The program analyses the squad and prints the formation with the highest score.

### Example
A sample squad file is included under `tests/data/sample_squad.html`.  
You can test the tool with:

```bash
python -m fm24_tool tests/data/sample_squad.html
```

Typical output:

```
Best formation: 4-4-2 (score 75.00/100)
```

## Optional: Run Tests
To verify the installation run the test suite:

```bash
pytest
```
