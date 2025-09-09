import re
from collections import defaultdict
import os

# 🌍 CONFIG: Change these to match your export language
PAGE_KEYWORD = "página"      # e.g., "page", "Seite", "pagina", "страница"
POSITION_KEYWORD = "posición" # e.g., "location", "posizione", "Position", "Lage"

# Convert Roman numerals to integers (for sorting)
def roman_to_int(roman):
    """Convert Roman numeral string to integer. Returns None if invalid."""
    roman = roman.upper()
    values = {
        'I': 1, 'V': 5, 'X': 10, 'L': 50,
        'C': 100, 'D': 500, 'M': 1000
    }
    total = 0
    prev_value = 0
    for char in reversed(roman):
        if char not in values:
            return None
        value = values[char]
        if value < prev_value:
            total -= value
        else:
            total += value
        prev_value = value
    return total

def clean_book_title(raw_title):
    """Clean and normalize book title + author.
    Removes (z-lib.org), (Z-Library), extra parentheses, and normalizes format to 'Title, Author'"""

    # Remove known garbage domains and source tags
    raw_title = re.sub(r'\s*\(z-lib\.org\)', '', raw_title, flags=re.IGNORECASE)
    raw_title = re.sub(r'\s*\(Z-Library\)', '', raw_title, flags=re.IGNORECASE)
    raw_title = re.sub(r'\s*\(www\.\w+\.com\)', '', raw_title, flags=re.IGNORECASE)
    raw_title = re.sub(r'\s*\(.*?source.*?\)', '', raw_title, flags=re.IGNORECASE)

    # Split by parentheses to extract parts
    parts = re.split(r'[()]', raw_title)
    parts = [p.strip() for p in parts if p.strip()]

    if not parts:
        return "Unknown Book"

    # First part is likely the title
    title = parts[0]

    # Try to find the most complete author name (usually last non-empty, non-role part)
    author = ""
    for part in reversed(parts[1:]):
        # Skip parts that look like roles (translator, editor, etc.)
        if (len(part) > 2 and
            not re.search(r'(ed|trans|translator|editor|comp|adapt|illus|version)', part, re.IGNORECASE)):
            author = part
            break

    # If no author found, try the first part after title
    if not author and len(parts) > 1:
        author = parts[1]

    # Clean author: replace underscores with spaces, normalize whitespace
    author = re.sub(r'_', ' ', author).strip()
    author = re.sub(r'\s+', ' ', author)

    # Format: "Title, Author" — if author exists
    if author:
        clean_title = f"{title}, {author}"
    else:
        clean_title = title

    # Final cleanup: remove trailing comma, keep only safe characters
    clean_title = re.sub(r'\s*,\s*$', '', clean_title)
    clean_title = re.sub(r'[^\w\s,\-]', ' ', clean_title)  # Replace unsafe chars with space
    clean_title = re.sub(r'\s+', ' ', clean_title).strip()

    return clean_title

print("=== PROCESSING FILE ===")

# ⚡️ Kindle exports are always named "My Clippings.txt" — no need to rename!
input_file = 'My Clippings.txt'

# Check if file exists
if not os.path.exists(input_file):
    print(f"❌ Error: File '{input_file}' not found.")
    print("💡 Please copy 'My Clippings.txt' from your Kindle to this folder.")
    exit(1)

# Read the file
with open(input_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Split content by separator '=========='
entries = content.split('==========')
print(f"📊 Total entries found: {len(entries)}")

# Dictionary to group quotes by book
quotes_by_book = defaultdict(list)
unprocessed_entries = []

def clean_title_for_filename(title):
    """Convert book title into a valid filename"""
    name = re.sub(r'[^\w\s\(\)-]', '', title)      # Remove special chars
    name = re.sub(r'\s+', ' ', name).strip()       # Normalize spaces
    name = name.replace(' ', '_')                  # Replace spaces with underscores
    if len(name) > 50:
        name = name[:50]                           # Limit length
    return name

def extract_book_title(lines):
    """Extract book title from first line, cleaning invisible characters"""
    if lines:
        first_line = lines[0].strip()
        # Clean invisible Unicode chars (BOM, zero-width, etc.)
        first_line = re.sub(r'^[\ufeff\u200b\u200c\u200d\ufeff﻿]+', '', first_line)
        if first_line:
            return first_line
    return "Unknown_Book"

# Process each entry
for idx, entry in enumerate(entries):
    if not entry.strip():
        continue

    lines = entry.strip().split('\n')
    entry_processed = False

    # Extract and clean book title
    raw_title = extract_book_title(lines)
    book_title = clean_book_title(raw_title)

    # Debug: show structure of first 3 entries
    if idx < 3:
        print(f"\n--- DEBUG: Entry {idx+1} ---")
        print(f"Raw title: '{raw_title}'")
        print(f"Clean title: '{book_title}'")
        for i, line in enumerate(lines[:4]):
            print(f"Line {i}: '{line}'")

    # Search for page or position number anywhere in the entry
    page_found = False
    for i, line in enumerate(lines):
        page_number = None
        page_num_int = None
        page_label_prefix = "page"

        # FIRST: Try PAGE (Arabic or Roman)
        match_page_arabic = re.search(rf'{PAGE_KEYWORD}\s*(\d+)', line, re.IGNORECASE)
        match_page_roman = re.search(rf'{PAGE_KEYWORD}\s*([ivxlcdm]+)', line, re.IGNORECASE)

        if match_page_arabic:
            page_number = match_page_arabic.group(1)
            page_num_int = int(page_number)
            page_label_prefix = PAGE_KEYWORD
        elif match_page_roman:
            roman_str = match_page_roman.group(1)
            page_num_int = roman_to_int(roman_str)
            if page_num_int is not None:
                page_number = roman_str
                page_label_prefix = PAGE_KEYWORD

        # SECOND: If no page found, try POSITION
        if page_num_int is None:
            match_pos = re.search(rf'{POSITION_KEYWORD}\s*(\d+)', line, re.IGNORECASE)
            if match_pos:
                page_number = match_pos.group(1)
                page_num_int = int(page_number)
                page_label_prefix = POSITION_KEYWORD

        # If still nothing found, skip this line
        if page_num_int is None:
            continue

        page_label = f"{page_label_prefix} {page_number}"

        # Search for quote in following lines
        quote = ""
        for j in range(i + 1, min(i + 3, len(lines))):
            candidate_line = lines[j].strip()

            # Clean invisible chars at start
            clean_line = re.sub(r'^[\ufeff\u200b\u200c\u200d\ufeff﻿]+', '', candidate_line)
            # Clean invisible chars anywhere in line
            clean_line = re.sub(r'[\ufeff\u200b\u200c\u200d\ufeff﻿\xa0]+', ' ', clean_line).strip()

            # Validate: not metadata, not empty, not separator
            if (clean_line and
                len(clean_line) >= 1 and
                not clean_line.startswith('-') and
                not 'posición' in candidate_line and
                not 'Añadido el' in candidate_line and
                not '==========' in candidate_line and
                not candidate_line.strip() == ''):

                quote = clean_line
                break  # ✅ Found quote — exit loop

        if quote:
            quotes_by_book[book_title].append({
                'page': page_label,
                'quote': quote,
                'page_num': page_num_int  # Used for sorting
            })
            # Silently mark as processed — no verbose output
            entry_processed = True
            page_found = True
        else:
            print(f"⚠️  {page_label} found but no valid quote in entry {idx+1}")
            # Debug: show candidate lines
            print("   Lines after metadata:")
            for debug_j in range(i + 1, min(i + 4, len(lines))):
                if debug_j < len(lines):
                    debug_line = lines[debug_j]
                    clean_debug = re.sub(r'^[\ufeff\u200b\u200c\u200d\ufeff﻿]+', '', debug_line.strip())
                    print(f"     Line {debug_j}: '{debug_line.strip()}' → Clean: '{clean_debug}' (len: {len(clean_debug)})")

        break  # Exit line loop — we found and processed (or tried)

    if not entry_processed and not page_found and entry.strip():
        unprocessed_entries.append((idx+1, book_title, entry.strip()[:1000] + "..."))

# Sort quotes by page/position number within each book
for book in quotes_by_book:
    quotes_by_book[book].sort(key=lambda x: x['page_num'])

# Create output directory if it doesn't exist
output_dir = 'books_by_title'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Create separate files for each book
created_files = []
for book, quotes in quotes_by_book.items():
    # Generate clean filename
    clean_filename = clean_title_for_filename(book)
    file_path = f"{output_dir}/{clean_filename}.txt"

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f"📚 {book}\n")
        f.write(f"{'='*60}\n")
        f.write(f"Total quotes: {len(quotes)}\n\n")

        for quote_info in quotes:
            f.write(f"{quote_info['page']}\n")
            f.write(f"{quote_info['quote']}\n\n")

    created_files.append((file_path, len(quotes)))
    print(f"📁 Created: {file_path} ({len(quotes)} quotes)")

# Save unprocessed entries to a separate file
if unprocessed_entries:
    unprocessed_file = f"{output_dir}/no-processed.txt"
    with open(unprocessed_file, 'w', encoding='utf-8') as f:
        f.write("⚠️ UNPROCESSED ENTRIES (could not extract page/position or quote)\n")
        f.write("="*70 + "\n\n")
        for idx, (entry_num, book_title, content) in enumerate(unprocessed_entries, 1):
            f.write(f"🔸 Entry #{entry_num} | Book: {book_title}\n")
            f.write("-" * 50 + "\n")
            f.write(content + "\n")
            f.write("\n" + "="*50 + "\n\n")
    print(f"📄 Saved {len(unprocessed_entries)} unprocessed entries to '{unprocessed_file}'")
    created_files.append((unprocessed_file, len(unprocessed_entries)))

print(f"\n=== FINAL RESULTS ===")
total_quotes = sum(len(quotes) for quotes in quotes_by_book.values())
print(f"✅ Processed {total_quotes} quotes from {len(quotes_by_book)} books")
print(f"📂 Created {len(created_files)} files in folder '{output_dir}/'")

# Final stats
total_valid_entries = len([e for e in entries if e.strip()])
success_rate = (total_quotes / total_valid_entries * 100) if total_valid_entries > 0 else 0
print(f"\n📈 Success rate: {success_rate:.1f}% ({total_quotes}/{total_valid_entries})")
print(f"📂 Check folder '{output_dir}/' to see your files")

print("\n🎉 Processing complete! Happy citation and referencing!")
