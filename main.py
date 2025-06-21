import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import yt_dlp
import os
import re

# Tooltip helper
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tipwindow or not self.text:
            return
        x, y, _, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + cy + self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify='left', background="#ffffe0",
                         relief='solid', borderwidth=1, font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

# Format options
format_options = [
    ("1080p", "bestvideo[height<=1080]+bestaudio/best[height<=1080]"),
    ("720p", "bestvideo[height<=720]+bestaudio/best[height<=720]"),
    ("480p", "bestvideo[height<=480]+bestaudio/best[height<=480]"),
    ("360p", "bestvideo[height<=360]+bestaudio/best[height<=360]"),
    ("Audio Only", "bestaudio")
]
format_display = [opt[0] for opt in format_options]
format_map = {opt[0]: opt[1] for opt in format_options}

# Validate YouTube URL
def is_valid_youtube_url(url):
    pattern = re.compile(r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/(watch\?v=|shorts/)?[\w-]{11,}")
    return bool(pattern.match(url))

# Main download logic
def download_video(url, format_var, progress_bar, progress_percent, root, save_path_var, download_btn, clear_btn):
    if not url or not is_valid_youtube_url(url):
        root.after(0, lambda: messagebox.showerror("Invalid URL", "Please enter a valid YouTube video or Shorts URL."))
        return
    # Disable UI
    root.config(cursor="wait")
    download_btn.config(state='disabled')
    clear_btn.config(state='disabled')
    # Set progress bar color to green (always, even after download)
    try:
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('green.Horizontal.TProgressbar', foreground='green', background='green')
        progress_bar.config(style='green.Horizontal.TProgressbar')
    except Exception:
        pass
    progress_bar.config(mode='indeterminate')
    progress_bar.start(10)

    format_code = format_map.get(format_var.get(), "best")

    def progress_hook(d):
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            if total > 0:
                percent = downloaded / total * 100
            else:
                percent = 0
            root.after(0, lambda: update_progress_ui(progress_bar, progress_percent, percent))
        elif d['status'] == 'finished':
            root.after(0, lambda: [
                update_progress_ui(progress_bar, progress_percent, 100),
                progress_bar.config(style='green.Horizontal.TProgressbar')
            ])

    ydl_opts = {
        'format': format_code,
        'outtmpl': os.path.join(save_path_var.get(), '%(title)s.%(ext)s'),
        'quiet': True,
        'noprogress': True,
        'progress_hooks': [progress_hook],
    }

    try:
        progress_bar.stop()
        progress_bar.config(mode='determinate')
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        root.after(0, lambda: [
            messagebox.showinfo("Download Complete", "The video has been downloaded successfully!"),
            progress_bar.config(style='green.Horizontal.TProgressbar')
        ])
    except Exception:
        progress_bar['value'] = 0
        progress_percent.config(text="0%")
    finally:
        root.config(cursor="")
        download_btn.config(state='normal')
        clear_btn.config(state='normal')
        # Do NOT reset progress bar style here

def update_progress_ui(progress_bar, progress_percent, percent):
    progress_bar['value'] = percent
    progress_percent.config(text=f"{percent:.1f}%")

def start_download(url_entry, format_var, progress_bar, progress_percent, root, save_path_var, download_btn, clear_btn):
    url = url_entry.get().strip()
    threading.Thread(
        target=download_video,
        args=(url, format_var, progress_bar, progress_percent, root, save_path_var, download_btn, clear_btn),
        daemon=True
    ).start()

def clear_form(url_entry, progress_bar, progress_percent):
    url_entry.delete(0, tk.END)
    progress_bar['value'] = 0
    progress_percent.config(text="0%")
    # Reset progress bar style to default
    try:
        progress_bar.config(style='TProgressbar')
    except Exception:
        pass

def choose_folder(save_path_var, root):
    folder = filedialog.askdirectory(parent=root, title="Select Download Folder")
    if folder:
        save_path_var.set(folder)

def main():
    root = tk.Tk()
    root.title("YouTube Downloader")
    root.geometry("440x320")
    root.resizable(False, False)

    style = ttk.Style()
    style.theme_use('clam')
    style.configure('TButton', font=("Segoe UI", 10))
    style.configure('TLabel', font=("Segoe UI", 10))
    style.configure('Header.TLabel', font=("Segoe UI", 16, "bold"))
    style.configure("TProgressbar", thickness=16)

    # Title
    title_label = ttk.Label(root, text="YouTube Video Downloader", style='Header.TLabel')
    title_label.pack(pady=(18, 8))

    # Main frame
    main_frame = ttk.Frame(root)
    main_frame.pack(padx=24, pady=4, fill='x', expand=True)

    # URL Entry
    url_label = ttk.Label(main_frame, text="YouTube Video or Shorts URL:")
    url_label.grid(row=0, column=0, sticky='w', pady=6)
    url_entry = ttk.Entry(main_frame, width=38)
    url_entry.grid(row=0, column=1, sticky='ew', pady=6, padx=(6, 0))
    ToolTip(url_entry, "Paste the full YouTube video or Shorts URL here.")

    # Format selection
    format_label = ttk.Label(main_frame, text="Format:")
    format_label.grid(row=1, column=0, sticky='w', pady=6)
    format_var = tk.StringVar(value=format_display[0])
    format_combo = ttk.Combobox(main_frame, textvariable=format_var, values=format_display, state='readonly', width=18)
    format_combo.grid(row=1, column=1, sticky='w', pady=6, padx=(6, 0))
    ToolTip(format_combo, "Choose the download quality or audio only.")

    # Save location
    save_path_var = tk.StringVar(value=os.getcwd())
    save_label = ttk.Label(main_frame, text="Save to:")
    save_label.grid(row=2, column=0, sticky='w', pady=6)
    save_entry = ttk.Entry(main_frame, textvariable=save_path_var, width=28, state='readonly')
    save_entry.grid(row=2, column=1, sticky='w', pady=6, padx=(6, 0))
    browse_btn = ttk.Button(main_frame, text="Browse", command=lambda: choose_folder(save_path_var, root), width=8)
    browse_btn.grid(row=2, column=1, sticky='e', pady=6, padx=(0, 0))
    ToolTip(browse_btn, "Choose the folder to save downloads.")
    main_frame.columnconfigure(1, weight=1)

    # Progress Bar with label overlay
    progress_frame = ttk.Frame(root)
    progress_frame.pack(pady=(10, 0), padx=24, fill='x')

    progress_bar = ttk.Progressbar(progress_frame, orient='horizontal', mode='determinate', length=340, maximum=100)
    progress_bar.pack(fill='x')
    progress_percent = ttk.Label(progress_frame, text="0%", anchor='center', font=("Segoe UI", 9, "bold"))
    progress_percent.place(relx=0.5, rely=0.5, anchor='center')

    # Button frame
    btn_frame = ttk.Frame(root)
    btn_frame.pack(pady=10)
    download_btn = ttk.Button(btn_frame, text="Download", width=14)
    download_btn.grid(row=0, column=0, padx=6)
    clear_btn = ttk.Button(btn_frame, text="Clear", width=10)
    clear_btn.grid(row=0, column=1, padx=6)
    download_btn.config(command=lambda: start_download(url_entry, format_var, progress_bar, progress_percent, root, save_path_var, download_btn, clear_btn))
    clear_btn.config(command=lambda: clear_form(url_entry, progress_bar, progress_percent))

    root.mainloop()

if __name__ == "__main__":
    main()