import speech_recognition as sr
import moviepy.editor as mp
import sys
import os
from pydub import AudioSegment
from pydub.silence import split_on_silence
import threading


r = sr.Recognizer()
# files
src = "./audios/doce sonho eu voz.mp3"
dst = "test.wav"


# convert wav to mp3
def convert_mp3_to_wav(src, dst):
    sound = AudioSegment.from_mp3(src)
    sound.export(dst, format="wav")
    return sound


def run_threaded(job_func, name: str, args: list):
    # Only one thread per populator/customerAPI is allowed
    if name not in [thread.name for thread in threading.enumerate()]:
        job_thread = threading.Thread(target=job_func, args=args, name=name)
        job_thread.start()
    else:
        print(f"Thread {name} already running.")


def transcribe_large_audio(path):
    """Split audio into chunks and apply speech recognition"""
    # Open audio file with pydub
    print("Reading MP3 audio file...")

    sound = convert_mp3_to_wav(path, f"{path[:-4]}.wav")
    # sound = AudioSegment.from_wav(f"{path[:-4]}.wav")

    # Split audio where silence is 700ms or greater and get chunks
    print("Splitting audio into chunks...")
    chunks = split_on_silence(
        sound, min_silence_len=700, silence_thresh=sound.dBFS - 14, keep_silence=700
    )

    # Create folder to store audio chunks
    print("Creating audio chunks folder...")
    file_name = f"{path[:-4]}".split("/")[-1]
    print(f"{file_name=}")
    folder_name = f"./audio-chunks/{file_name}"
    print(folder_name)
    if not os.path.isdir(folder_name):
        if not os.path.isdir(f"./audio-chunks"):
            os.mkdir(f"./audio-chunks")
        os.mkdir(folder_name)

    whole_text = ""

    # Process each chunk
    for i, audio_chunk in enumerate(chunks, start=1):
        # Export chunk and save in folder
        print(f"Exporting chunk {i}...")
        chunk_filename = os.path.join(folder_name, f"chunk{i}.wav")
        audio_chunk.export(chunk_filename, format="wav")

        # Recognize chunk
        print(f"Recognizing chunk {i}...")
        with sr.AudioFile(chunk_filename) as source:
            audio_listened = r.record(source)
            # Convert to text
            try:
                text = r.recognize_google(audio_listened, language="pt-BR")
            except sr.UnknownValueError as e:
                print("Error:", str(e))
                text = f"[ERRO UNKNOWN] {e}"
            except sr.RequestError as e:
                print("Error request:", str(e))
                text = f"[ERRO REQUEST] {e}"
            except Exception as e:
                print("Error exception:", str(e))
                text = f"[ERRO EXCEPT] {e}"
            finally:
                text = f"{text.capitalize()}. "
                print(chunk_filename, ":", text)
                whole_text += text

    # Return text for all chunks
    return whole_text


def transcribe_and_write(file_ts, folder):
    path = f"{folder}/{file_ts}"

    print("Transcribe large audio file...")
    print(path)
    result = transcribe_large_audio(path)

    print(result)
    file_name = f"{path[:-4]}".split("/")[-1]
    print(result, file=open(f"./textos/{file_name}.txt", "w"))
    print("ok")


folders = [x[0] for x in os.walk(f"./audios")]
for folder in folders:
    for file_input in os.listdir(folder):
        if file_input.endswith(".mp3"):
            c = f"{file_input[:-4]}.txt"
            if c not in os.listdir("./textos"):
                print(f"{file_input=}")
                run_threaded(
                    transcribe_and_write, name=file_input, args=(file_input, folder)
                )
