from flask import Flask, request, jsonify, send_file
from tempfile import TemporaryDirectory
from flask_cors import CORS
import yt_dlp
# import subprocess
import os
import re


DOWNLOAD_DIR = os.path.expanduser('~/Downloads/flask_downloads')

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# Create a temporary directory for the download
temp_dir = os.path.join(DOWNLOAD_DIR, "temp")
os.makedirs(temp_dir, exist_ok=True)

def sanitize_filename(filename):
    # Replace any character that is not alphanumeric, or a dot/underscore with an underscore
    sanitized = re.sub(r'[<>:"/\\|?*,\s(){}[\]-]', '_', filename)  # Replace invalid characters, whitespace, commas, hyphens, and brackets with '_'
    sanitized = re.sub(r'_+', '_', sanitized)  # Replace multiple consecutive underscores with a single underscore
    return sanitized

app = Flask(__name__)

CORS(app, resources={r"/*": {
    "origins": "*",  # Allow any origin
    "methods": ["GET", "POST", "OPTIONS"],  # Allow specific methods
    "allow_headers": "*",  # Allow any headers
    "expose_headers": ["Content-Disposition","Content-Length"]  # Expose specific headers
}})

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
        'noplaylist': True,
        'source_address': '0.0.0.0',
    }

    if quality == 'mp3':
        # Audio download options
        ydl_opts['format'] = 'bestaudio'
        ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]
    else:
        # Video download options
        quality_height = int(quality.rstrip('p')) # this removes p [720p => 720]
        ydl_opts['format'] = f'bestvideo[height={quality_height}]+bestaudio'
        ydl_opts['postprocessors']= [{'key': 'FFmpegVideoConvertor','preferedformat': 'mp4'}]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)

        # Sanitize the title for use in the filename
        sanitized_title = sanitize_filename(info_dict['title'])
        ydl_opts['outtmpl'] = os.path.join(temp_dir, f'{sanitized_title}.%(ext)s')  

        # Download the file with the updated outtmpl
        ydl = yt_dlp.YoutubeDL(ydl_opts)

        def hook(d):
            if d['status'] == 'finished':
                print('Done downloading:', d['filename'])
            elif d['status'] == 'downloading':
                total_bytes = d.get('total_bytes', None)
                downloaded_bytes = d.get('downloaded_bytes', 0)
                if total_bytes:
                    percentage = (downloaded_bytes / total_bytes) * 100
                    print(f"Download progress: {percentage:.2f}%")

        ydl.download([url])

        # Find the best format for audio or video
        if quality.lower() == 'mp3':            
            file_path = os.path.join(temp_dir, f"{sanitized_title}.mp3")
        else:
            file_path = os.path.join(temp_dir, f"{sanitized_title}.mp4")

        # Check if the downloaded file exists
        if os.path.exists(file_path):
            response = send_file(file_path, as_attachment=True)
            response.headers['Content-Length'] = os.path.getsize(file_path)
            return response
        else:
            return jsonify({'error': 'File not found after extraction.'}), 500

    except yt_dlp.utils.DownloadError as e:
        return jsonify({'error': 'Download failed: ' + str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'An error occurred: ' + str(e)}), 500



if __name__ == "__main__":
    app.run(debug=True)
