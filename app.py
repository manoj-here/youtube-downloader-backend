from flask import Flask, request, jsonify
import subprocess
import os
import yt_dlp

app = Flask(__name__)

@app.route("/check", methods=["POST"])
def get_video_formats():
    url = request.json.get("url")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    ydl_opts = {
        'noplaylist': True,  # Ignore playlists
        'source_address': '0.0.0.0', #enforce use of ipv4 for better speed.         
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            sanitized_info = ydl.sanitize_info(info)
            
            # Prepare a list to hold the available formats
            available_formats = []
            
            if 'formats' in sanitized_info:
                for format_info in sanitized_info['formats']:
                    # Create a formatted response for each available format
                    format_details = {
                        "ID": format_info.get("format_id"),  # Format ID
                        "resolution": (f"{format_info.get('width', 'N/A')}x{format_info.get('height', 'N/A')}" 
                                       if format_info.get('height') else "N/A"),  # Resolution
                        "ext": format_info.get("ext")  # File extension
                    }
                    available_formats.append(format_details)

                return jsonify(available_formats), 200  # Return all formats
            else:
                return jsonify({"error": "No available formats found"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
