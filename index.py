from flask import Flask, request, jsonify
from mutagen.mp3 import MP3
from PIL import Image
from pathlib import Path
import requests
import os
from io import BytesIO
import imageio
from moviepy import editor
import base64

app = Flask(__name__)
VIDEO_DIR = "videos"
os.makedirs(VIDEO_DIR, exist_ok=True)

@app.route('/generate_video', methods=['POST'])
def generate_video():
    data = request.json
    audio_url = data.get("audio_url")
    image_url = data.get("image_url")
    
    if not audio_url or not image_url:
        return jsonify({"error": "Missing audio or image URL"}), 400

    try:
        # Download audio
        audio_response = requests.get(audio_url)
        audio_path = os.path.join(VIDEO_DIR, "audio.mp3")
        with open(audio_path, "wb") as file:
            file.write(audio_response.content)
        
        # Get audio length
        audio = MP3(audio_path)
        audio_length = audio.info.length
        
        # Download image
        image_response = requests.get(image_url, timeout=10)
        image = Image.open(BytesIO(image_response.content)).convert("RGB")
        image = image.resize((400, 400), Image.Resampling.LANCZOS)
        
        # Create GIF
        gif_path = os.path.join(VIDEO_DIR, "images.gif")
        imageio.mimsave(gif_path, [image], duration=(audio_length * 1000))
        
        # Create video
        video_clip = editor.VideoFileClip(gif_path)
        audio_clip = editor.AudioFileClip(audio_path)
        final_video = video_clip.set_audio(audio_clip)
        
        video_path = os.path.join(VIDEO_DIR, "video.mp4")
        final_video.write_videofile(video_path, fps=20, codec="libx264", logger=None)
        print("about to ready")
        # Convert video to base64
        return jsonify({"video_url": request.host_url + "videos/video.mp4"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
