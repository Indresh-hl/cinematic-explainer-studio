import json
from PIL import ImageFont, ImageDraw, Image

def build_phrases(max_chars=22):
    font = ImageFont.truetype('assets/fonts/PlayfairDisplay.ttf', 88)
    dummy = ImageDraw.Draw(Image.new('RGBA', (100, 100)))

    data = json.load(open('assets/full_timeline_word_timestamps.json'))
    phrases = []
    
    for seg in data['segments']:
        words = seg.get('words', [])
        if not words: continue
        i = 0
        while i < len(words):
            # Decide chunk size: 2 or 3 words based on character length
            take = 2
            if i + 3 <= len(words):
                three_words = words[i:i+3]
                char_len = sum(len(w['word']) for w in three_words)
                if char_len <= max_chars and (len(words) - i) != 4:
                    take = 3
            elif (len(words) - i) == 3:
                take = 3
            else:
                take = len(words) - i
                
            chunk = words[i:i+take]
            text = ' '.join([w['word'] for w in chunk])
            bbox = dummy.textbbox((0, 0), text, font=font)
            pw = bbox[2] - bbox[0]
            
            p_start = chunk[0]['start']
            p_end = chunk[-1]['end'] + (0.20 if i+take >= len(words) else 0.05)
            
            phrases.append({
                'start': p_start,
                'end': p_end,
                'words': chunk,
                'text': text,
                'pw': pw
            })
            i += take

    print(f"Total phrases: {len(phrases)}")
    max_p = max(phrases, key=lambda x: x['pw'])
    print(f"Max phrase width: {max_p['pw']}px -> '{max_p['text']}'")
    widths = [p['pw'] for p in phrases]
    print(f"Average width: {sum(widths)/len(widths):.1f}px")
    print(f"Phrases > 750px: {sum(1 for w in widths if w > 750)}")
    return phrases

if __name__ == "__main__":
    build_phrases()
