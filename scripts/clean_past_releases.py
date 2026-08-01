#!/usr/bin/env python3
"""
clean_past_releases.py — Clean ANSI escape codes and debug artifacts from past GitHub Releases.
"""

import subprocess
import json
import re
import sys
import argparse

def strip_ansi(text):
    # Strip ANSI escape sequences (both raw bytes and literal caret representations)
    ansi_escape = re.compile(r'(?:\x1b|\\x1b|\\u001b|\^\[)\[[0-9;]*[a-zA-Z]')
    return ansi_escape.sub('', text)

def clean_body(body):
    # Strip ANSI escape sequences
    cleaned = strip_ansi(body)
    
    # Strip any leading 'Here' and following whitespace/newlines
    cleaned = re.sub(r'^Here\s*\n+', '', cleaned)
    
    # Strip trailing whitespace/newlines
    cleaned = cleaned.strip()
    
    return cleaned

def main():
    parser = argparse.ArgumentParser(description="Clean ANSI escape codes and debug artifacts from past GitHub Releases.")
    parser.add_argument("--run", action="store_true", help="Actually execute the edits on GitHub (default is dry-run)")
    args = parser.parse_args()

    print("Fetching releases from GitHub...")
    res = subprocess.run(['gh', 'release', 'list', '--limit', '100'], capture_output=True, text=True, check=True)
    
    tags = []
    for line in res.stdout.strip().split('\n'):
        if line:
            parts = line.split('\t')
            if len(parts) >= 3:
                tags.append(parts[2])

    print(f"Found {len(tags)} releases.")
    
    modified_count = 0
    for tag in tags:
        res = subprocess.run(['gh', 'release', 'view', tag, '--json', 'body'], capture_output=True, text=True)
        if res.returncode != 0:
            print(f"Warning: Failed to fetch release for tag {tag}")
            continue
        
        try:
            data = json.loads(res.stdout)
        except json.JSONDecodeError:
            print(f"Warning: Failed to parse JSON for tag {tag}")
            continue
            
        body = data.get('body', '')
        cleaned = clean_body(body)
        
        if body != cleaned:
            print(f"\n==========================================")
            print(f"Tag: {tag} NEEDS CLEANING")
            print(f"==========================================")
            print("--- Original ---")
            print(repr(body[:200]) + ("..." if len(body) > 200 else ""))
            print("--- Cleaned ---")
            print(repr(cleaned[:200]) + ("..." if len(cleaned) > 200 else ""))
            
            modified_count += 1
            if args.run:
                print(f"Updating release {tag} on GitHub...")
                edit_res = subprocess.run(['gh', 'release', 'edit', tag, '--notes-file', '-'], input=cleaned, capture_output=True, text=True)
                if edit_res.returncode == 0:
                    print(f"Successfully updated tag {tag}")
                else:
                    print(f"Error updating tag {tag}: {edit_res.stderr.strip()}", file=sys.stderr)
            else:
                print("[DRY RUN] Use --run to apply changes.")
                
    print(f"\nScan complete. {modified_count} out of {len(tags)} releases need changes.")

if __name__ == "__main__":
    main()
