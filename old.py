from moviepy.editor import *
import whisper_timestamped
import sys

CLIP_DUR = 5 # change this for shorter/longer intervals between intertitles
if(len(sys.argv) == 3):
    CLIP_DUR = int(sys.argv[2])

# reads video file
vid = VideoFileClip(f"inputs\\{sys.argv[1]}")
vid = vid.fx(vfx.blackwhite)
vid.fps = 24

if(vid.duration < CLIP_DUR):
    CLIP_DUR = vid.duration

# reads audio file and creates timestamped transcript
vid.audio.write_audiofile("inputs\\audio.mp3")
model = whisper_timestamped.load_model("base")
res = whisper_timestamped.transcribe(model, "inputs\\audio.mp3")
file = open("outputs\\transcript.txt", "w")
file.write(res["text"])

# creates reusable clip for dialogue cards ("intertitles")
card = ImageClip("inputs\\intertitle.png", duration=vid.duration)
card = card.fx(vfx.resize, width=vid.w)
card = card.fx(vfx.margin, top=(vid.h-card.h)//2, bottom=(vid.h-card.h)//2 if (vid.h-card.h)%2==0 else ((vid.h-card.h)//2)+1)
card.fps = 24

subclips = int(vid.duration)//CLIP_DUR
clips = []

final = None

# creates dict to map subclip number to line of text during said subclip
text_dict = {key: None for key in range(0, subclips)}

for i in range(0, subclips):
    # makes sure video is not cut short by including any extra seconds in last subclip
    max_cdur = CLIP_DUR
    if(i == subclips-1):
        max_cdur = CLIP_DUR + vid.duration%CLIP_DUR
        
    text = ""
    for seg in res['segments']:
        for word in seg['words']:
            if word['start'] >= i*CLIP_DUR and word['start'] < (i*CLIP_DUR)+max_cdur:
                text = text + word['text'] + " "
    text_dict[i] = text[0:len(text)-1]

# matches each subclip with a corresponding intertitle
for i in range(0, subclips):
    max_cdur = CLIP_DUR
    if(i == subclips-1):
        max_cdur = CLIP_DUR + vid.duration%CLIP_DUR
    
    clip1 = vid.subclip(i*CLIP_DUR, (i*CLIP_DUR)+max_cdur)
    clip2 = card.subclip(i*CLIP_DUR, (i*CLIP_DUR)+max_cdur)

    # determines text spoken in subclip using text_dict
    text = TextClip(text_dict[i], font='century-schoolbook', fontsize=20*card.w/400, color='white', method="caption", size=(card.w, card.h)).set_pos('center').set_duration(max_cdur)
    text = text.fx(vfx.resize, 0.8)

    dialogue = CompositeVideoClip([clip2, text])
    combo = concatenate_videoclips([clip1, dialogue])

    filename = "temp\\temp" + str(i) + ".mp4"
    combo.write_videofile(filename)
    clips.append(filename)

song = AudioFileClip("inputs\\song.mp3")
# unnecessarily fucking long line of code!! :3
# this loops the song if necessary, manages volume, and fades out the audio
music = concatenate_audioclips([song for i in range(0, int(2*vid.duration/song.duration)+1)]).subclip(0,2*vid.duration).fx(afx.volumex, 0.2).fx(afx.audio_fadeout, 0.5)

final = concatenate_videoclips([VideoFileClip(f) for f in clips])
final.audio = music
final.write_videofile('outputs\\silent.mp4')