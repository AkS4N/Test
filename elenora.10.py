import openai
import time
import requests
import json
import keyboard
from gtts import gTTS
import os
import speech_recognition as sr
import pyaudio
import wave
from playsound import playsound
import pytchat
import threading
import emoji
import re
import winsound
import subprocess
from pydub import AudioSegment
from pydub.playback import play

# tambahkan API Key OpenAI 
openai.api_key = "Masukan disini"

#Tambahkan API Key ElevenLab
eleven_api = "Masukan Disini"


def membuat_subtitle():
    # Clear the text files after the assistant has finished speaking
    time.sleep(1)
    with open("output.txt", "w") as f:
        f.truncate(0)
    with open("chat.txt", "w") as f:
        f.truncate(0)


conversation = []
# Create a dictionary to hold the message data
history = {"history": conversation}

mode = 0
total_characters = 0
chat = ""
chat_now = ""
chat_prev = ""
is_Speaking = False
owner_name = "Sandi"
blacklist = ["Nightbot", "streamelements"]


def membuat_respon(prompt):
    respon = openai.Completion.create(
        engine="text-davinci-003",
        max_tokens=4000,
        n=1,
        stop=None,
        temperature=0.5,
        prompt=prompt,
    )
    return respon["choices"][0]["text"]


def transcribe_audio(input_wav):
    r = sr.Recognizer()
    with sr.AudioFile(input_wav) as source:
        audio = r.record(source)
    try:
        text = r.recognize_google(audio, language="id-ID")
        print("User: " + text)
        return text
    except sr.UnknownValueError:
        print("Maaf, aku tidak dapat memahami apa yang kamu katakan.")
        return ""
    except sr.RequestError as e:
        print("Maaf, service speech recognition sedang tidak tersedia; {0}".format(e))
        return ""


# function to get the user's input audio
def record_audio():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    WAVE_OUTPUT_FILENAME = "input.wav"
    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK
    )
    frames = []
    print("Recording...")
    frames = []
    while keyboard.is_pressed("RIGHT_SHIFT"):
        data = stream.read(CHUNK)
        frames.append(data)
    print("Stopped recording.")
    stream.stop_stream()
    stream.close()
    p.terminate()
    wf = wave.open("input.wav", "wb")
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b"".join(frames))
    wf.close()

    membuat_subtitle()  # Tambahkan pemanggilan fungsi membuat_subtitle() di sini


def main():
    # membuat variabel untuk menyimpan mode yang dipilih
    mode_terpilih = None

    while True:
        # jika mode belum dipilih sebelumnya, minta pengguna memilih mode
        if mode_terpilih is None:
            print("Silakan pilih mode:")
            print("1. Suara")
            print("2. Tulis")
            print("3. Live youtube")
            print("4. Keluar")

            mode_terpilih = input()

            # validasi pilihan pengguna
            while mode_terpilih not in ["1", "2", "3", "4"]:
                print("Mohon masukkan pilihan yang benar")
                mode_terpilih = input()

        # melakukan tindakan sesuai dengan mode yang dipilih
        if mode_terpilih == "1":
            print("Press and Hold Right Shift to record audio")
            while True:
                if keyboard.is_pressed("RIGHT_SHIFT"):
                    record_audio()
                    text = transcribe_audio("input.wav")
                    # Simpan pertanyaan ke dalam file chat.txt
                    with open("chat.txt", "a") as f:
                        f.write("User: " + text + "\n")
                    # membuat respon menggunakan OpenAI
                    prompt = "User: " + text + "\nElenora:"
                    respon = membuat_respon(prompt)
                    print("Elenora: " + respon)
                    # Simpan jawaban ke dalam file output.txt
                    with open("output.txt", "a") as f:
                        f.write("Elenora: " + respon + "\n")
                    speak_text(respon)
                    membuat_subtitle()  # Tambahkan pemanggilan fungsi membuat_subtitle() di sini
                    break

        elif mode_terpilih == "2":
            # mode tulis
            text = input("Apa pertanyaanmu...")
            # Simpan pertanyaan ke dalam file chat.txt
            with open("chat.txt", "a") as f:
                f.write("User: " + text + "\n")
            # membuat respon menggunakan OpenAI
            prompt = "User: " + text + "\nElenora:"
            respon = membuat_respon(prompt)
            print("Elenora: " + respon)
            # Simpan jawaban ke dalam file output.txt
            with open("output.txt", "a") as f:
                f.write("Elenora: " + respon + "\n")
            speak_text(respon)

            membuat_subtitle()  # Tambahkan pemanggilan fungsi membuat_subtitle() di sini

        elif mode_terpilih == "3":
            # mode live youtube
            live_id = input("Livestream ID: ")
            # Threading is used to capture livechat and answer the chat at the same time
            t = threading.Thread(target=preparation)
            t.start()
            yt_livechat(live_id)

        elif mode_terpilih == "4":
            # keluar dari program
            break


# function to capture livechat from youtube
def yt_livechat(video_id):
    global chat

    live = pytchat.create(video_id=video_id)
    while live.is_alive():
        try:
            for c in live.get().sync_items():
                if c.author.name in blacklist:
                    continue
                message = c.message.lower()
                # Menghapus emoji dari pesan
                message = emoji.demojize(message)

                print(f"{c.author.name}: {message}")

                # Simpan input ke dalam file chat.txt
                with open("chat.txt", "a") as f:
                    f.write(f"{c.author.name}: {message}\n")

                # Membuat respon menggunakan OpenAI
                prompt = f"{c.author.name}: {message}\nElenora:"
                respon = membuat_respon(prompt)
                print("Elenora: " + respon)

                # Simpan output ke dalam file output.txt
                with open("output.txt", "a") as f:
                    f.write("Elenora: " + respon + "\n")

                speak_text(respon)

                membuat_subtitle()  # Tambahkan pemanggilan fungsi membuat_subtitle() di sini
        except Exception as e:
            print("Exception occurred: ", e)


def preparation():
    global conversation, chat_now, chat, chat_prev
    while True:
        # If the assistant is not speaking, and the chat is not empty, and the chat is not the same as the previous chat
        # then the assistant will answer the chat
        chat_now = chat
        if is_Speaking == False and chat_now != chat_prev:
            # Saving chat history
            conversation.append({"role": "user", "content": chat_now})
            chat_prev = chat_now
            membuat_respon(prompt)
            print("Elenora: " + respon)
            speak_text(respon)
        time.sleep(1)

def speak_text(text):
    # Define the API endpoint URL
    url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM?optimize_streaming_latency=0"

    # Define the request headers
    headers = {
        "accept": "audio/mpeg",
        "xi-api-key": eleven_api,
        "Content-Type": "application/json",
    }

    # Define the request payload
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0, "similarity_boost": 0},
    }

    # Send the POST request to the API
    response = requests.post(url, headers=headers, data=json.dumps(payload))

    # Check if the request was successful
    if response.status_code == 200:
        # Save the response content as an MP3 file
        with open("output.mp3", "wb") as f:
            f.write(response.content)

        # Play the MP3 file using pydub
        sound = AudioSegment.from_mp3("output.mp3")
        play(sound)

    else:
        print("Error:", response.status_code)


if __name__ == "__main__":
    main()
