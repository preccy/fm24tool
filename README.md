# FM24 Squad Viewer

A minimalistic Python tool for displaying Football Manager 2024 squad data exported as HTML.

## Features
- Premium dark interface with blue accents and rounded controls
- Load squad HTML files and view them in a sortable table

- Rate common formations and all official tactical styles on a 1-100 scale
- Tabs highlighting the best, worst, and wonderkid players in the squad
- Position scoring uses weighted attributes based on FM-Arena testing
- "Assess My Squad" button that sends your squad data to ChatGPT for a written assessment


## Installation
```
pip install -r requirements.txt
```

## Usage
```
python main.py
```
Then click **Open Squad HTML** and choose an exported FM24 squad HTML file.

For squad assessments via ChatGPT, supply your OpenAI API key either by setting the `OPENAI_API_KEY` environment variable before launch or by clicking the ⚙ settings icon within the app and entering the key.

Use **Assess My Squad** to generate a summary of strengths, weak spots, and players to consider offloading.

Analysis tabs will populate once the file is loaded.

