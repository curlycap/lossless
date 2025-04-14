import sys
import os
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QTextEdit
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from pymediainfo import MediaInfo
import humanize


def format_size(size_in_bytes):
    return humanize.naturalsize(size_in_bytes, binary=True)


class MediaAnalyzer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Media Analyzer Pro 🔥")
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2f;
                color: #fff;
                font-family: Consolas;
                font-size: 14px;
            }
            QPushButton {
                background-color: #ff5c57;
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #ff2e2a;
            }
            QTextEdit {
                background-color: #2b2b3c;
                border-radius: 8px;
                padding: 10px;
            }
            .quality-premium {
                color: #4caf50;
                font-weight: bold;
            }
            .quality-good {
                color: #8bc34a;
            }
            .quality-medium {
                color: #ffc107;
            }
            .quality-low {
                color: #f44336;
            }
        """)

        layout = QVBoxLayout()

        self.label = QLabel("🎵 Select your media file")
        self.label.setAlignment(Qt.AlignCenter)

        self.button = QPushButton("Browse File")
        self.button.clicked.connect(self.select_file)

        self.result = QTextEdit()
        self.result.setReadOnly(True)

        layout.addWidget(self.label)
        layout.addWidget(self.button)
        layout.addWidget(self.result)

        self.setLayout(layout)

        # Animation
        self.fade = QPropertyAnimation(self, b"windowOpacity")
        self.fade.setDuration(800)
        self.fade.setStartValue(0)
        self.fade.setEndValue(1)
        self.fade.setEasingCurve(QEasingCurve.OutCubic)
        self.fade.start()

    def select_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Media File")
        if file:
            self.analyze_file(file)

    def analyze_file(self, file):
        info = MediaInfo.parse(file)
        output = f"<b>File:</b> {os.path.basename(file)}<br>{'='*60}<br>"

        duration_sec = 0
        audio_size_mb = 0
        audio_quality = "Unknown"
        quality_class = "quality-medium"
        is_high_res = False
        audio_bitrate = 0
        audio_samplerate = 0
        audio_bitdepth = 0

        for track in info.tracks:
            if track.track_type == "Audio":
                output += "<br><b>--- Audio Track ---</b><br>"
                output += f"<b>Codec:</b> {track.format}<br>"
                output += f"<b>Channels:</b> {track.channel_s}<br>"
                
                if hasattr(track, 'bit_depth') and track.bit_depth:
                    audio_bitdepth = int(track.bit_depth)
                    output += f"<b>Bit Depth:</b> {audio_bitdepth}-bit<br>"
                
                if track.bit_rate:
                    audio_bitrate = int(track.bit_rate)/1000
                    output += f"<b>Bitrate:</b> {audio_bitrate:.2f} kbps<br>"
                
                if track.sampling_rate:
                    audio_samplerate = int(track.sampling_rate)/1000
                    output += f"<b>Sampling Rate:</b> {audio_samplerate:.1f} kHz<br>"

                if track.duration and track.bit_rate:
                    duration_sec = float(track.duration) / 1000
                    audio_size_mb = (int(float(track.bit_rate)) * duration_sec) / 8 / 1024 / 1024
                    output += f"<b>Estimated Audio Size:</b> {audio_size_mb:.2f} MB<br>"

                # Determine audio quality
                codec = track.format.lower() if track.format else ""
                codec_id = track.codec_id.lower() if hasattr(track, 'codec_id') and track.codec_id else ""
                sampling_rate = int(track.sampling_rate) if track.sampling_rate else 0
                bit_depth = int(track.bit_depth) if hasattr(track, 'bit_depth') and track.bit_depth else 0

                # Lossless formats
                lossless_formats = ['flac', 'alac', 'pcm', 'wavpack', 'truehd', 'ape', 'wav', 'aiff', 'dsd']
                lossy_formats = {
                    'mp3': 'MP3',
                    'aac': 'AAC',
                    'ogg': 'OGG Vorbis',
                    'opus': 'Opus',
                    'vorbis': 'Vorbis',
                    'ac3': 'Dolby Digital',
                    'e-ac3': 'Dolby Digital Plus',
                    'dts': 'DTS'
                }

                # Check for MPEG Audio (MP3)
                if "mpeg audio" in codec or "mp3" in codec or "mp3" in codec_id:
                    audio_quality = f"Lossy ({lossy_formats['mp3']})"
                    quality_class = "quality-low" if audio_bitrate < 192 else "quality-medium"
                elif codec in lossless_formats:
                    audio_quality = "Lossless"
                    quality_class = "quality-good"
                    
                    # High-res lossless detection
                    if (sampling_rate > 48000 or bit_depth > 16) and codec not in lossy_formats:
                        audio_quality = "High-Resolution Lossless"
                        quality_class = "quality-premium"
                        is_high_res = True
                elif codec in lossy_formats:
                    audio_quality = f"Lossy ({lossy_formats[codec]})"
                    quality_class = "quality-low" if audio_bitrate < 192 else "quality-medium"
                else:
                    audio_quality = f"Unknown ({codec})"
                    quality_class = "quality-medium"

                # Quality assessment based on bitrate (for lossy formats)
                if "Lossy" in audio_quality and track.bit_rate:
                    if audio_bitrate >= 256:
                        audio_quality += " (High Quality)"
                        quality_class = "quality-good"
                    elif audio_bitrate >= 192:
                        audio_quality += " (Medium Quality)"
                    else:
                        audio_quality += " (Low Quality)"
                        quality_class = "quality-low"

        file_size = os.path.getsize(file)

        output += "<br><b>Detected Type:</b> "
        output += "Video File<br>" if any(t.track_type == "Video" for t in info.tracks) else "Audio File<br>"
        output += f"<br><b>Total File Size:</b> {format_size(file_size)}"
        output += f"<br><b>Duration:</b> {duration_sec:.2f} sec" if duration_sec else ""
        output += f'<br><b>Audio Quality:</b> <span class="{quality_class}">{audio_quality}</span>'
        
        # Additional quality notes
        if is_high_res:
            output += "<br><br>🔹 <span class='quality-premium'>Premium Quality</span>: This file meets high-resolution lossless standards"
        elif "Lossless" in audio_quality:
            output += "<br><br>🔹 <span class='quality-good'>Good Quality</span>: This is a standard lossless audio file"
        elif "High Quality" in audio_quality:
            output += "<br><br>🔹 <span class='quality-good'>Good Quality</span>: High bitrate lossy compression"
        elif "Low Quality" in audio_quality:
            output += "<br><br>⚠️ <span class='quality-low'>Notice</span>: Low quality lossy compression detected"
        elif "Unknown" in audio_quality:
            output += "<br><br>⚠️ <span class='quality-medium'>Notice</span>: Could not determine audio codec type"

        self.result.setHtml(output)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MediaAnalyzer()
    window.resize(600, 500)
    window.show()
    sys.exit(app.exec())