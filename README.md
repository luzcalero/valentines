# Relationship Text Visualization
A creative coding project that transforms WhatsApp chat history into an interactive visual story. The project analyzes text patterns, emotional content, and conversation dynamics to create an artistic representation of a relationship's journey through time.

## Overview

This project combines natural language processing with creative visualization to turn personal chat history into an interactive art piece. It processes bilingual (Spanish/English) WhatsApp conversations and maps words, phrases, and patterns to various visual elements like colors, shapes, and movements.

## Features

- WhatsApp chat history analysis
- Bilingual text processing (Spanish/English)
- Real-time particle animation system
- Interactive visualization controls
- Emotional content mapping
- Temporal pattern visualization

## Project Structure

```
relationship-viz/
├── src/
│   ├── analysis/
│   │   ├── chat_analyzer.py     # Text processing and analysis
│   │   └── visual_mapper.py     # Word-to-visual property mapping
│   ├── visualization/
│   │   ├── index.html          # Main visualization page
│   │   ├── sketch.js           # p5.js animation code
│   │   └── styles.css          # Visual styling
│   └── utils/
│       └── preprocessor.py      # Chat history preprocessing
├── data/
│   └── chat_export.txt         # Your WhatsApp chat export (not included)
├── examples/
│   └── demo.gif                # Visualization demo
└── docs/
    └── VISUALIZATION.md        # Detailed visualization documentation
```
