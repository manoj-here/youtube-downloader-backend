from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

@app.route('/check', methods=["POST"])
def check_video():
    url = request.json.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    ydl_opts = {
        'format': 'best',
        'outtmpl': '%(title)s.%(ext)s',  # Save as the video title
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            title = info_dict.get('title', None)
            return jsonify({"message": f"Downloaded '{title}' successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)