from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import yt_dlp
import whisper
import ffmpeg
 
load_dotenv() 
app = Flask(__name__)
 
def baixar_audio(youtube_url, output_path="audio.mp3"):
  """Baixa o áudio de um vídeo do YouTube e salva como MP3."""
  ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'outtmpl': output_path
  }

  with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([youtube_url])
 
    return output_path
 
def transcrever_audio(audio_path):
  """Transcreve o áudio usando Whisper."""
  model = whisper.load_model("base")  # Pode trocar por "tiny", "small", "medium", "large"
  result = model.transcribe(audio_path)
  return result["text"]
 
def main(youtube_url):
  print("🔄 Baixando o áudio do YouTube...")
  audio_path = baixar_audio(youtube_url)

  if os.path.exists(audio_path + ".mp3"):
    os.rename(audio_path + ".mp3", audio_path)

  print("📝 Transcrevendo o áudio...")
  texto_transcrito = transcrever_audio(audio_path)

  print("\n📜 Transcrição do vídeo:\n")
  print(texto_transcrito)
  
  # Remover o arquivo de áudio após a transcrição (opcional)
  os.remove(audio_path)
  return texto_transcrito
 
@app.route('/baixar-audio', methods=['POST'])
def get_link():
  try:
    data = request.json
    if not data or "link" not in data or not isinstance(data["link"], str):
      return jsonify({"error": "O campo 'link' é obrigatório e deve ser uma string."}), 400
    
    link = main(data["link"])

    return jsonify({"Transcrição:": link}), 200

  except Exception as e:
    return jsonify({"error": str(e)}), 500
 
if __name__ == '__main__':
  app.run(debug=True)