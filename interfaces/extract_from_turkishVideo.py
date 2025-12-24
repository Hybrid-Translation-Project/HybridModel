import library
def video_to_audio(video_path: str, audio_path: str):
    ffmpeg_path = library.shutil.which("ffmpeg")
    if not ffmpeg_path:
        raise FileNotFoundError("ffmpeg bulunamadı (PATH'e eklenmeli).")

    command = [
        ffmpeg_path,
        "-y",
        "-i", video_path,
        "-ar", "16000",
        "-ac", "1",
        audio_path
    ]

    library.subprocess.run(
        command,
        stdout=library.subprocess.DEVNULL,
        stderr=library.subprocess.DEVNULL,
        check=True
    )


def audio_to_text(audio_path: str, txt_path: str):
    model = library.whisper.load_model("large-v3")
    result = model.transcribe(audio_path, language="tr")

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(result["text"])


# 🔴 UI'NİN ÇAĞIRACAĞI TEK FONKSİYON
def extract_tr_video_to_txt(video_path: str, output_txt_path: str):
    temp_wav = library.os.path.splitext(output_txt_path)[0] + "_tmp.wav"

    try:
        video_to_audio(video_path, temp_wav)
        audio_to_text(temp_wav, output_txt_path)
    finally:
        if library.os.path.exists(temp_wav):
            library.os.remove(temp_wav)
