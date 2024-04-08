from moviepy.editor import *
import whisper_timestamped
import sys

# reads video file
vid = VideoFileClip(f"inputs\\{sys.argv[1]}")
vid = vid.fx(vfx.blackwhite)
vid.fps = 24

# reads audio file and creates timestamped transcript
vid.audio.write_audiofile("inputs\\audio.mp3")
model = whisper_timestamped.load_model("base")
res = whisper_timestamped.transcribe(model, "inputs\\audio.mp3")
file = open("outputs\\transcript.txt", "w")
file.write(res["text"])

# creates reusable clip for dialogue cards ("intertitles")
card = ImageClip("inputs\\intertitle.png", duration=vid.duration+len(res['segments']))
card = card.fx(vfx.resize, width=vid.w)
card = card.fx(vfx.margin, top=(vid.h-card.h)//2, bottom=(vid.h-card.h)//2 if (vid.h-card.h)%2==0 else ((vid.h-card.h)//2)+1)
card.fps = 24

# creates dict to map subclip start to line of text during said subclip
text_dict = {key: None for key in range(0, len(res['segments']))}
dur_dict = {key: None for key in range(0, len(res['segments']))}
clips = []

c = 0
for seg in res['segments']:
    text = ""
    i = 0
    start = 0
    dur = 0
    for word in seg['words']:
        if(i == 0):
            start = word['start']
        if(i == len(seg['words'])-1):
            end = word['end']
            dur_dict[c] = [start, end]

        text += word['text'] + " "
        i += 1
    
    text_dict[c] = text[0:len(text)-1]
    c += 1

# matches each subclip with a corresponding intertitle
total_dur = 0
for i in range(0, len(text_dict)):
    start = dur_dict[i][0]
    end = dur_dict[i][1]
    dur_text = max(1, end-start)
    
    if(i == 0):
        start = 0
    if(i == len(text_dict)-1):
        end = vid.duration
    
    total_dur += end-start + dur_text
    
    clip1 = vid.subclip(start, end)
    clip2 = card.subclip(dur_dict[i][0], (dur_dict[i][0]+1 if dur_text == 1 else dur_dict[i][1]))

    # determines text spoken in subclip using text_dict
    text = TextClip(text_dict[i], font='century-schoolbook', fontsize=20*card.w/400, color='white', method="caption", size=(card.w, card.h)).set_pos('center').set_duration(dur_text)
    text = text.fx(vfx.resize, 0.8)

    dialogue = CompositeVideoClip([clip2, text])
    combo = concatenate_videoclips([clip1, dialogue])

    filename = f"temp\\temp{str(i)}.mp4"
    combo.write_videofile(filename)
    clips.append(filename)

song = AudioFileClip("inputs\\song.aac")
song = song.subclip(0, song.duration-5)

# this loops the song if necessary, manages volume, and fades out the audio
music = concatenate_audioclips([song for i in range(0, int(total_dur/(song.duration))+1)]).subclip(0, total_dur).fx(afx.volumex, 0.2).fx(afx.audio_fadeout, 1)

final = concatenate_videoclips([VideoFileClip(f) for f in clips])
final.audio = music
final.write_videofile(f"outputs\\{sys.argv[1][:-4]}.mp4")