import yt_dlp

def download_video(url, output_filename):
    ydl_opts = {
        'format': 'best',
        'outtmpl': output_filename,
        # NETWORK & RETRY SETTINGS
        'fragment_retries': 50,       # Retry a failed fragment 50 times before giving up
        'retries': 20,                # Retry HTTP 20 times on connection errors
        'socket_timeout': 60,         # Wait 60 seconds before timing out (default is often shorter)
        'ignoreerrors': True,         # If a fragment is truly dead, skip it and finish the video anyway
        'concurrent_fragment_downloads': 1, # Download 1 at a time to be gentler on the server
    }

    try:
        print(f"Starting download from: {url}")
        print("Settings: High retries and timeouts enabled...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print(f"\nSuccess! Video saved as {output_filename}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    url = "https://stream.videodb.io/v3/published/manifests/2081539d-bc65-4e59-becb-e7ff945f0d1d.m3u8"
    download_video(url, "downloaded_video.mp4")