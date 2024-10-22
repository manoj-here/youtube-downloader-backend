from flask import Flask, request, jsonify, send_file
from tempfile import TemporaryDirectory
from flask_cors import CORS
import yt_dlp
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

    # default flags (options)
    ydl_opts = {
        'outtmpl': '%(title)s.%(ext)s',
        'noplaylist': True,
        'source_address': '0.0.0.0',
    }

    if quality == 'mp3':
        # Audio download options
        ydl_opts['format'] = 'bestaudio'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        # Video download options
        return jsonify({"message": "video processing under-developement!"}), 200

    # Create a temporary directory to store the downloaded file
    with TemporaryDirectory() as tmpdirname:
        ydl_opts['outtmpl'] = os.path.join(tmpdirname, '%(title)s.%(ext)s')

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                # Get the info dictionary
                info_dict = ydl.extract_info(url, download=False)

            # Check for the downloaded audio file
            if quality == 'mp3':
                # Construct the expected MP3 file path
                audio_file_path = os.path.join(tmpdirname, f"{info_dict['title']}.mp3")
            else:
                # For video formats, use the correct extension based on quality
                video_file_path = os.path.join(tmpdirname, f"{info_dict['title']}.{quality.split('p')[0]}")  # Assuming it follows naming convention
                audio_file_path = video_file_path  # Use the same path if it's a video format

            # Check if the audio file exists
            if os.path.exists(audio_file_path):
                return send_file(audio_file_path, as_attachment=True)
            else:
                return jsonify({'error': 'File not found after extraction.'}), 500

        except Exception as e:
            return jsonify({'error': str(e)}), 500



if __name__ == "__main__":
    app.run(debug=True)
