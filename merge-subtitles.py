import os
import json
import difflib
import sys

# Input Files
WHISPER_FILE = "whisper_subtitles.txt"
MANUAL_FILE = "manual_subtitles.txt"

# Output Files
OUTPUT_MERGED_TXT = "final_subtitles.txt"
OUTPUT_MERGED_JSON = "final_subtitles.json"
OUTPUT_REPORT = "merge_report.txt"

# Merge Strategy
PREFER_MANUAL_TEXT = True  # True = manual text preferred
PREFER_WHISPER_TIMING = True  # True = Whisper timing preferred
SIMILARITY_THRESHOLD = 0.6  # 60% similarity to match


def read_subtitle_file(filename):
    """Read subtitle file and parse"""
    print(f"\n Reading: {filename}")
    
    if not os.path.exists(filename):
        print(f"  File not found: {filename}")
        return []
    
    subtitles = []
    
    with open(filename, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            try:
                parts = [p.strip() for p in line.split('|')]
                
                if len(parts) < 4:
                    continue
                
                subtitles.append({
                    'index': int(parts[0]),
                    'start': float(parts[1]),
                    'end': float(parts[2]),
                    'text': parts[3],
                    'line_num': line_num
                })
                
            except Exception as e:
                print(f"⚠️  Line {line_num}: Parse error - {e}")
    
    print(f" Loaded {len(subtitles)} subtitles")
    return subtitles


def calculate_text_similarity(text1, text2):
    """Calculate similarity between two texts"""
    # Remove spaces and normalize
    t1 = text1.replace(' ', '').strip()
    t2 = text2.replace(' ', '').strip()
    
    if not t1 or not t2:
        return 0.0
    
    # Use sequence matcher
    return difflib.SequenceMatcher(None, t1, t2).ratio()


def find_best_match(whisper_sub, manual_subs, used_indices):
    """Find best matching manual subtitle for whisper subtitle"""
    best_match = None
    best_score = 0.0
    
    for manual_sub in manual_subs:
        # Skip already used
        if manual_sub['index'] in used_indices:
            continue
        
        # Calculate text similarity
        text_sim = calculate_text_similarity(
            whisper_sub['text'], 
            manual_sub['text']
        )
        
        # Calculate timing proximity (closer = better)
        time_diff = abs(whisper_sub['start'] - manual_sub['start'])
        time_score = max(0, 1 - (time_diff / 5.0))  # 5 second window
        
        # Combined score (70% text, 30% timing)
        combined_score = (text_sim * 0.7) + (time_score * 0.3)
        
        if combined_score > best_score and combined_score >= SIMILARITY_THRESHOLD:
            best_score = combined_score
            best_match = manual_sub
    
    return best_match, best_score


def merge_subtitles(whisper_subs, manual_subs):
    """Intelligently merge whisper and manual subtitles"""
    print(f"\n Merging subtitles...")
    print(f"   Strategy: Manual text={'YES' if PREFER_MANUAL_TEXT else 'NO'}, "
          f"Whisper timing={'YES' if PREFER_WHISPER_TIMING else 'NO'}")
    
    merged = []
    used_manual_indices = set()
    merge_stats = {
        'perfect_match': 0,
        'fuzzy_match': 0,
        'whisper_only': 0,
        'manual_only': 0
    }
    
    # Process Whisper subtitles
    for w_sub in whisper_subs:
        manual_match, score = find_best_match(w_sub, manual_subs, used_manual_indices)
        
        if manual_match:
            # Found a match
            used_manual_indices.add(manual_match['index'])
            
            merged_sub = {
                'index': len(merged) + 1,
                'start': w_sub['start'] if PREFER_WHISPER_TIMING else manual_match['start'],
                'end': w_sub['end'] if PREFER_WHISPER_TIMING else manual_match['end'],
                'text': manual_match['text'] if PREFER_MANUAL_TEXT else w_sub['text'],
                'source': 'merged',
                'match_score': score,
                'whisper_text': w_sub['text'],
                'manual_text': manual_match['text']
            }
            
            if score > 0.9:
                merge_stats['perfect_match'] += 1
            else:
                merge_stats['fuzzy_match'] += 1
        else:
            # No match - use Whisper only
            merged_sub = {
                'index': len(merged) + 1,
                'start': w_sub['start'],
                'end': w_sub['end'],
                'text': w_sub['text'],
                'source': 'whisper_only',
                'match_score': 0.0,
                'whisper_text': w_sub['text'],
                'manual_text': None
            }
            merge_stats['whisper_only'] += 1
        
        merged.append(merged_sub)
    
    # Add unmatched manual subtitles
    for m_sub in manual_subs:
        if m_sub['index'] not in used_manual_indices:
            merged.append({
                'index': len(merged) + 1,
                'start': m_sub['start'],
                'end': m_sub['end'],
                'text': m_sub['text'],
                'source': 'manual_only',
                'match_score': 0.0,
                'whisper_text': None,
                'manual_text': m_sub['text']
            })
            merge_stats['manual_only'] += 1
    
    # Sort by start time
    merged.sort(key=lambda x: x['start'])
    
    # Re-index
    for i, sub in enumerate(merged, 1):
        sub['index'] = i
    
    return merged, merge_stats


def save_merged_txt(subtitles, filename):
    """Save merged subtitles in TXT format"""
    print(f"\n Saving: {filename}")
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("# Final Merged Subtitles\n")
        f.write("# Format: start | end | text\n\n")
        
        for sub in subtitles:
            f.write(f"{sub['start']:.2f} | {sub['end']:.2f} | {sub['text']}\n")
    
    print(f" Saved: {filename}")


def save_merged_json(subtitles, filename):
    """Save merged subtitles in JSON format (with metadata)"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(subtitles, f, indent=2, ensure_ascii=False)
    print(f" Backup saved: {filename}")


def save_merge_report(stats, merged_subs, filename):
    """Save detailed merge report"""
    print(f"\n Saving merge report: {filename}")
    
    with open(filename, 'w', encoding='utf-8') as f:
      
        f.write("SUBTITLE MERGE REPORT\n")
        
        
        f.write("MERGE STATISTICS:\n")
        f.write(f"  Perfect matches: {stats['perfect_match']}\n")
        f.write(f"  Fuzzy matches: {stats['fuzzy_match']}\n")
        f.write(f"  Whisper only: {stats['whisper_only']}\n")
        f.write(f"  Manual only: {stats['manual_only']}\n")
        f.write(f"  Total: {len(merged_subs)}\n\n")
        
  
        f.write("DETAILED COMPARISON:\n")
   
        
        for sub in merged_subs:
            f.write(f"\n[{sub['index']}] {sub['start']:.2f}s - {sub['end']:.2f}s\n")
            f.write(f"Source: {sub['source']}\n")
            if sub['match_score'] > 0:
                f.write(f"Match score: {sub['match_score']:.2%}\n")
            f.write(f"Final text: {sub['text']}\n")
            
            if sub['whisper_text']:
                f.write(f"Whisper: {sub['whisper_text']}\n")
            if sub['manual_text']:
                f.write(f"Manual: {sub['manual_text']}\n")
            f.write("-" * 70 + "\n")
    
    print(f" Report saved: {filename}")


def main():

    print("    INTELLIGENT SUBTITLE MERGER")
  
    
    # Read files
    whisper_subs = read_subtitle_file(WHISPER_FILE)
    manual_subs = read_subtitle_file(MANUAL_FILE)
    
    if not whisper_subs and not manual_subs:
        print("\n Error: No subtitle files found!")
        return
    
    if not whisper_subs:
        print("\n  Warning: No Whisper subtitles, using manual only")
        merged_subs = manual_subs
        stats = {'manual_only': len(manual_subs), 'perfect_match': 0, 'fuzzy_match': 0, 'whisper_only': 0}
    elif not manual_subs:
        print("\n  Warning: No manual subtitles, using Whisper only")
        merged_subs = whisper_subs
        stats = {'whisper_only': len(whisper_subs), 'perfect_match': 0, 'fuzzy_match': 0, 'manual_only': 0}
    else:
        # Merge both
        merged_subs, stats = merge_subtitles(whisper_subs, manual_subs)
    
    # Save results
    save_merged_txt(merged_subs, OUTPUT_MERGED_TXT)
    save_merged_json(merged_subs, OUTPUT_MERGED_JSON)
    save_merge_report(stats, merged_subs, OUTPUT_REPORT)
  


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user")
        sys.exit(0)