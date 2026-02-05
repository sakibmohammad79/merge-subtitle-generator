from moviepy import VideoFileClip
import whisper
import json
import os
import sys

VIDEO_PATH = "Beautiful Recitation of Surah Infitar (سورة الانفطار_).mp4"

# Whisper Settings
WHISPER_MODEL = "large-v3"
LANGUAGE = "ar"            
TASK = "transcribe"          

# Output Files
OUTPUT_WHISPER_TXT = "whisper_subtitles.txt"
OUTPUT_WHISPER_JSON = "whisper_subtitles.json"
SUBTITLE_DELAY = 1.0

def extract_audio_from_video(video_path):
    video = VideoFileClip(video_path)
    audio_file = "temp_audio.wav"
    
    video.audio.write_audiofile(
        audio_file, 
        codec='pcm_s16le',
        logger=None
    )
    
    video.close()
    print(f"Audio extracted: {audio_file}")
    return audio_file


def transcribe_with_whisper(audio_file, language, task):
    """Transcribe audio using Whisper AI"""
    print(f"\n Loading Whisper AI model: {WHISPER_MODEL}")
    
    model = whisper.load_model(WHISPER_MODEL)
    print(" Model loaded successfully!")
    
    print(f"\nTranscribing audio...")
    print(f"   Language: {language}")
    print(f"   Word-level timestamps: Enabled")
    print("   This may take several minutes...")
    
    result = model.transcribe(
        audio_file,
        language=language,
        task=task,
        word_timestamps=False,
        no_speech_threshold=0.6,
        condition_on_previous_text=False,
        verbose=False
    )
    
    print(f"Transcription complete!")
    return result


# def process_word_level_subtitles(result, delay):
#     """Process word-by-word subtitles from Whisper"""
#     print(f"\nProcessing word-level subtitles...")
    
#     subtitles = []
#     word_index = 0
    
#     for segment in result['segments']:
#         if 'words' in segment and segment['words']:
#             for word in segment['words']:
#                 word_index += 1
#                 subtitles.append({
#                     'index': word_index,
#                     'text': word['word'].strip(),
#                     'start': round(word['start'] + delay, 2),
#                     'end': round(word['end'] + delay, 2),
#                     'duration': round(word['end'] - word['start'], 2),
#                     'source': 'whisper'
#                 })
    
#     return subtitles


def save_txt_format(subtitles, filename):
    """Save subtitles in TXT format"""
    print(f"\nSaving: {filename}")
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("# Whisper Auto-Generated Subtitles\n")
        f.write("# Format: index | start | end | text\n")
        f.write("# This is automatic - may need corrections\n\n")
        
        for sub in subtitles:
            f.write(f"{sub['index']} | {sub['start']:.2f} | {sub['end']:.2f} | {sub['text']}\n")
    
    print(f"Saved: {filename}")


def save_json_format(subtitles, filename):
    """Save subtitles in JSON format"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(subtitles, f, indent=2, ensure_ascii=False)
    print(f"Backup saved: {filename}")


def preview_subtitles(subtitles, count=10):
    """Show preview"""
    print(f"PREVIEW (First {count} of {len(subtitles)})")

    for i, sub in enumerate(subtitles[:count], 1):
        print(f"{i}. [{sub['start']:.1f}s - {sub['end']:.1f}s] {sub['text']}")
    
    if len(subtitles) > count:
        print(f"\n... and {len(subtitles) - count} more")



def main():
    if not os.path.exists(VIDEO_PATH):
        print(f"\nError: Video file not found: {VIDEO_PATH}")
        return
    
    print(f"\nVideo found: {VIDEO_PATH}")
    
    try:
        # Step 1: Extract audio
        audio_file = extract_audio_from_video(VIDEO_PATH)
        
        # Step 2: Transcribe
        subtitles = transcribe_with_whisper(audio_file, LANGUAGE, TASK)
        
        # Step 3: Process
        # subtitles = process_word_level_subtitles(result, SUBTITLE_DELAY)
        
        # Step 4: Preview
        preview_subtitles(subtitles)
        
        # Step 5: Save
        save_txt_format(subtitles, OUTPUT_WHISPER_TXT)
        save_json_format(subtitles, OUTPUT_WHISPER_JSON)
        
        # Cleanup
        if os.path.exists(audio_file):
            os.remove(audio_file)
        
        print("\n" + "="*70)
        print("SUCCESS! Whisper subtitles created!")
        print("="*70)
        print(f"\nGenerated: {OUTPUT_WHISPER_TXT}")
        print(f"Total words: {len(subtitles)}")
 
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if os.path.exists("temp_audio.wav"):
            try:
                os.remove("temp_audio.wav")
            except:
                pass

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user")
        sys.exit(0)