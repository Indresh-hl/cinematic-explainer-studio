import asyncio
import os
import edge_tts

ACT1_TEXT = """
It is 2:14 in the morning.

Your room is completely silent. Your body is physically exhausted. Every single problem from your waking day has finally vanished.

And then... without warning... your brain pulls an old, dusty reel out of the archives.

That awkward sentence you muttered in middle school.

The high-five you accidentally offered to someone who was going for a fist bump.

Or that presentation four years ago where your voice cracked, and you completely forgot your own boss's name.

Instantly, your stomach drops. Your face feels burning hot against the cold pillow. You physically grimace in the dark, curling into a ball as if the humiliation happened thirty seconds ago.

Why now?

Why did your brain decide that 2:00 in the morning—the exact moment you need sleep more than anything on earth—was the perfect time to host a film festival of your greatest personal failures?

Most people assume this nocturnal torture is a cruel glitch. A biological flaw in human design.

But modern neuroscience reveals something far more fascinating.

Your brain isn't trying to punish you.

It's running an ancient, life-or-death survival simulation.
""".strip()

async def generate():
    voice = "en-US-ChristopherNeural"
    rate = "-3%"
    pitch = "-2Hz"
    
    output_dir = os.path.join(os.path.dirname(__file__), "audio")
    os.makedirs(output_dir, exist_ok=True)
    mp3_file = os.path.join(output_dir, "act1_voiceover.mp3")
    srt_file = os.path.join(output_dir, "act1_subtitles.srt")
    
    submaker = edge_tts.SubMaker()
    communicate = edge_tts.Communicate(ACT1_TEXT, voice, rate=rate, pitch=pitch)
    
    with open(mp3_file, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.feed(chunk)
                
    with open(srt_file, "w", encoding="utf-8") as f:
        f.write(submaker.get_srt())
        
    print(f"Generated Audio: {mp3_file}")
    print(f"Generated Subtitles: {srt_file}")

if __name__ == "__main__":
    asyncio.run(generate())
