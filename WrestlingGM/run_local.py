# run_local.py — launches The Booking Room as a local desktop app
import threading
import webview
from app import app   # your existing Flask app, untouched

def start_flask():
    # debug=False is important — no reloader inside the packaged app
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    # 1. Flask runs in the background
    t = threading.Thread(target=start_flask, daemon=True)
    t.start()

    # 2. A native window opens pointing at the local server
    webview.create_window(
        'The Booking Room',
        'http://127.0.0.1:5000',
        width=1280,
        height=860,
        min_size=(900, 600),
    )
    webview.start()
