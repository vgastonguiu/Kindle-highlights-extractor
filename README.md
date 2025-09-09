# Kindle Highlights Extractor

Extracts and organizes highlights/quotes from Kindle´s myclippings.txt into separate files per book.

## Problem
Kindle generates a file, myclippings.txt, where it dumps highlights from all books that you read chronologically rather than by book, and adds long, unnecessary strings to your highlight bloating the content. I needed a way to quickly sort the highlights by book for future reference, and to erase Kindle´s additional metadata.

## Features
- Separates mixed highlights from multiple books that Kindle collects in myclippings.txt by detecting the separator ==========
- Groups quotes by book title and arranges them by page vs chronologically
- Handles both long quotes and individual vocabulary words
- Sorts highlights by page number
- Erases unnecessary and repetitive information from the invidivual highlights
- Cleans invisible Unicode characters
- Creates one .txt file per book
- Shows stats and unprocessed entries
     

## Language Support

By default, the script looks for the word **“página”** (Spanish) to find page numbers.
✏**To use with other languages**, edit this line at the top of the script `kindle_quotes_extractor.py`:

```python
PAGE_KEYWORD = "página"  # ← CHANGE THIS!

## Development
Developed with assistance from Claude AI and Qwen AI for refinement and implementation.
