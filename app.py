from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import logging
import subprocess
import os

app = Flask(__name__)
CORS(app)

@app.route("/check", methods=["POST"])
def get_video_formats():
    url = request.json.get("url")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    ydl_opts = {
        'noplaylist': True,
        'source_address': '0.0.0.0',  # equivalent of --force-ipv4 flag, gives you best speed possible.
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            sanitized_info = ydl.sanitize_info(info)

            # Initialize booleans for audio and video
            audio_exists = False
            video_resolutions = set()
            response = []

            # Iterate over the formats to extract necessary information
            for fmt in sanitized_info['formats']:                
                if fmt.get("acodec", 'none') != 'none' and not audio_exists:
                    response.append({
                        "icon": "bx bxs-music",
                        "quality": "mp3"
                    })
                    audio_exists = True

                # Convert video resolutions to general quality terms
                resolution = fmt.get("resolution")
                if fmt.get("vcodec", 'none') != 'none':
                    # Check for common resolutions and add them
                    if resolution == "640x360":
                        video_resolutions.add("360p")
                    elif resolution == "854x480":
                        video_resolutions.add("480p")
                    elif resolution == "1280x720":
                        video_resolutions.add("720p")
                    elif resolution == "1920x1080":
                        video_resolutions.add("1080p")
                    elif resolution == "2560x1440":
                        video_resolutions.add("1440p")
                    elif resolution == "3840x2160":
                        video_resolutions.add("2160p")

            # Create a mapping from resolution labels to numerical values
            resolution_mapping = {
                "360p": 360,
                "480p": 480,
                "720p": 720,
                "1080p": 1080,
                "1440p": 1440,
                "2160p": 2160,
            }
            # Sort the video_resolutions based on their numerical values
            # because unmanaged structures annoys me. 
            sorted_resolutions = sorted(video_resolutions, key=lambda x: resolution_mapping[x])

            # Add unique video resolutions to the response unique means no duplicate. 
            for quality in sorted_resolutions:
                response.append({
                    "icon": "bx bxs-video",
                    "quality": quality
                })

            return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================================#
#------  CHECK PART IS WORKING FINE -------#
# =========================================#



@app.route("/download", methods=["POST"])
def download_video():
    data = request.json
    url = data.get('url')
    quality = data.get('quality')

    logging.info(f"Received download request for URL: {url} with quality: {quality}")

    # I will do it later 😅 too tired.

    return jsonify({"message": "Download in progress..."})



if __name__ == "__main__":
    app.run(debug=True)
