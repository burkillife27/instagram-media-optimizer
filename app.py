import os
import sys
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox

# Try importing customtkinter, fallback to standard tkinter if needed
try:
    import customtkinter as ctk
    HAS_CTK = True
except ImportError:
    HAS_CTK = False

from optimizer import (
    optimize_image,
    optimize_video,
    generate_output_path,
    get_ffmpeg_path
)

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif', '.heic'}
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.mkv', '.avi', '.m4v', '.webm'}

class InstagramOptimizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Instagram Medya Optimize Edici (Ultra HD)")
        self.root.geometry("860x720")
        self.root.minsize(780, 600)

        self.selected_files = []
        self.is_processing = False

        self._setup_ui()

    def _setup_ui(self):
        if HAS_CTK:
            ctk.set_appearance_mode("Dark")
            ctk.set_default_color_theme("blue")
            self._setup_ctk_ui()
        else:
            self._setup_tk_ui()

    def _setup_ctk_ui(self):
        # Header Frame
        header = ctk.CTkFrame(self.root, corner_radius=10, fg_color=("#2b2b2b", "#1e1e1e"))
        header.pack(fill="x", padx=16, pady=(16, 10))

        title = ctk.CTkLabel(
            header,
            text="✨ Instagram Medya Optimize Edici",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(anchor="w", padx=16, pady=(10, 2))

        desc = ctk.CTkLabel(
            header,
            text="Görsel ve videoları Instagram'ın bozmayacağı ideal sRGB, Lanczos ve H.264 formatında sıkıştırır.\nOrijinal dosyalara dokunmaz; aynı klasöre sonuna '_insta' ekleyerek kaydeder.",
            font=ctk.CTkFont(size=12),
            text_color="gray70",
            justify="left"
        )
        desc.pack(anchor="w", padx=16, pady=(0, 10))

        # Main Layout: Two Columns (Files on left, Settings on right)
        main_content = ctk.CTkFrame(self.root, fg_color="transparent")
        main_content.pack(fill="both", expand=True, padx=16, pady=5)

        # LEFT COLUMN: File List & Buttons
        left_frame = ctk.CTkFrame(main_content, corner_radius=10)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=0)

        file_btn_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        file_btn_frame.pack(fill="x", padx=12, pady=12)

        add_files_btn = ctk.CTkButton(
            file_btn_frame,
            text="📁 Dosya(lar) Ekle",
            command=self.browse_files,
            width=130,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        add_files_btn.pack(side="left", padx=(0, 8))

        add_folder_btn = ctk.CTkButton(
            file_btn_frame,
            text="📂 Klasör Ekle",
            command=self.browse_folder,
            width=120,
            fg_color="#3e4a59",
            hover_color="#4f5e70"
        )
        add_folder_btn.pack(side="left", padx=(0, 8))

        clear_btn = ctk.CTkButton(
            file_btn_frame,
            text="🗑️ Temizle",
            command=self.clear_files,
            width=80,
            fg_color="#802b2b",
            hover_color="#993333"
        )
        clear_btn.pack(side="right")

        # Scrollable file list
        self.file_listbox = ctk.CTkTextbox(left_frame, font=ctk.CTkFont(family="Consolas", size=12), wrap="none")
        self.file_listbox.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        self.file_listbox.insert("1.0", "Henüz dosya eklenmedi...\nYukarıdaki butonlarla görsel veya video ekleyebilirsiniz.\n(Desteklenenler: JPG, PNG, WEBP, MP4, MOV, vb.)")
        self.file_listbox.configure(state="disabled")

        self.file_count_lbl = ctk.CTkLabel(left_frame, text="0 dosya seçildi", text_color="gray70", font=ctk.CTkFont(size=12))
        self.file_count_lbl.pack(anchor="w", padx=14, pady=(0, 10))

        # RIGHT COLUMN: Settings
        right_frame = ctk.CTkFrame(main_content, width=320, corner_radius=10)
        right_frame.pack(side="right", fill="y", padx=(8, 0), pady=0)
        right_frame.pack_propagate(False)

        settings_title = ctk.CTkLabel(right_frame, text="⚙️ Optimizasyon Ayarları", font=ctk.CTkFont(size=15, weight="bold"))
        settings_title.pack(anchor="w", padx=16, pady=(14, 10))

        # 1. Preset Selector
        ctk.CTkLabel(right_frame, text="1. Hedef Format:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=16, pady=(6, 2))
        self.preset_var = ctk.StringVar(value="Dikey Post (4:5 | 1080x1350) ⭐")
        self.preset_menu = ctk.CTkOptionMenu(
            right_frame,
            variable=self.preset_var,
            values=[
                "Dikey Post (4:5 | 1080x1350) ⭐",
                "Reels & Hikaye (9:16 | 1080x1920)",
                "Kare Post (1:1 | 1080x1080)",
                "Yatay Post (1.91:1 | 1080x566)",
                "Orijinal Oran (Maks. 1080px)"
            ]
        )
        self.preset_menu.pack(fill="x", padx=16, pady=(0, 8))

        # 2. Fit Mode
        ctk.CTkLabel(right_frame, text="2. Çerçeveye Sığdırma:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=16, pady=(6, 2))
        self.fit_var = ctk.StringVar(value="Bulanık Arka Plan (Kesmez)")
        self.fit_menu = ctk.CTkOptionMenu(
            right_frame,
            variable=self.fit_var,
            values=[
                "Bulanık Arka Plan (Kesmez)",
                "Kırparak Doldur (Crop & Fill)",
                "Siyah Çerçeveli Sığdır",
                "Beyaz Çerçeveli Sığdır"
            ]
        )
        self.fit_menu.pack(fill="x", padx=16, pady=(0, 8))

        # 3. Sharpening
        ctk.CTkLabel(right_frame, text="3. Akıllı Netleştirme (Fotoğraf):", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=16, pady=(6, 2))
        self.sharpen_var = ctk.StringVar(value="Orta (Önerilen)")
        self.sharpen_menu = ctk.CTkOptionMenu(
            right_frame,
            variable=self.sharpen_var,
            values=[
                "Hafif",
                "Orta (Önerilen)",
                "Güçlü",
                "Kapalı"
            ]
        )
        self.sharpen_menu.pack(fill="x", padx=16, pady=(0, 8))

        # 4. Quality
        ctk.CTkLabel(right_frame, text="4. Kalite Seviyesi:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=16, pady=(6, 2))
        self.quality_var = ctk.StringVar(value="Ultra HD (%88 - İdeal)")
        self.quality_menu = ctk.CTkOptionMenu(
            right_frame,
            variable=self.quality_var,
            values=[
                "Ultra HD (%92)",
                "Ultra HD (%88 - İdeal)",
                "Dengeli (%82)"
            ]
        )
        self.quality_menu.pack(fill="x", padx=16, pady=(0, 14))

        # Open folder checkbox
        self.open_folder_var = ctk.BooleanVar(value=True)
        self.open_folder_cb = ctk.CTkCheckBox(
            right_frame,
            text="Bittiğinde çıktı klasörünü aç",
            variable=self.open_folder_var,
            font=ctk.CTkFont(size=12)
        )
        self.open_folder_cb.pack(anchor="w", padx=16, pady=(0, 10))

        # BOTTOM: Action & Progress
        bottom_frame = ctk.CTkFrame(self.root, corner_radius=10)
        bottom_frame.pack(fill="x", padx=16, pady=(5, 16))

        self.start_btn = ctk.CTkButton(
            bottom_frame,
            text="🚀 OPTİMİZE ET VE KAYDET",
            command=self.start_processing,
            font=ctk.CTkFont(size=15, weight="bold"),
            height=44,
            fg_color="#8a3ab9",
            hover_color="#bc2a8d"
        )
        self.start_btn.pack(fill="x", padx=16, pady=(12, 8))

        self.progress_bar = ctk.CTkProgressBar(bottom_frame)
        self.progress_bar.pack(fill="x", padx=16, pady=(0, 6))
        self.progress_bar.set(0)

        self.status_lbl = ctk.CTkLabel(
            bottom_frame,
            text="Hazır. Optimize edilecek medyaları seçin.",
            font=ctk.CTkFont(size=12),
            text_color="gray70"
        )
        self.status_lbl.pack(anchor="w", padx=16, pady=(0, 10))

    def _setup_tk_ui(self):
        # Fallback to standard Tkinter if CustomTkinter fails
        pass

    def browse_files(self):
        filetypes = [
            ("Tüm Desteklenen Medyalar", "*.jpg;*.jpeg;*.png;*.webp;*.bmp;*.mp4;*.mov;*.mkv;*.avi;*.m4v"),
            ("Fotoğraflar", "*.jpg;*.jpeg;*.png;*.webp;*.bmp;*.heic"),
            ("Videolar", "*.mp4;*.mov;*.mkv;*.avi;*.m4v"),
            ("Tüm Dosyalar", "*.*")
        ]
        files = filedialog.askopenfilenames(
            title="Instagram İçin Medya Seçin",
            filetypes=filetypes
        )
        if files:
            for f in files:
                f_norm = os.path.normpath(f)
                if f_norm not in self.selected_files:
                    self.selected_files.append(f_norm)
            self._update_file_list_view()

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Medya Klasörü Seçin")
        if folder:
            count_added = 0
            for root_dir, _, filenames in os.walk(folder):
                for fname in filenames:
                    ext = os.path.splitext(fname)[1].lower()
                    if ext in IMAGE_EXTENSIONS or ext in VIDEO_EXTENSIONS:
                        # Avoid adding files that already end in _insta
                        if "_insta" in os.path.splitext(fname)[0]:
                            continue
                        full_path = os.path.normpath(os.path.join(root_dir, fname))
                        if full_path not in self.selected_files:
                            self.selected_files.append(full_path)
                            count_added += 1
            self._update_file_list_view()

    def clear_files(self):
        self.selected_files.clear()
        self._update_file_list_view()

    def _update_file_list_view(self):
        self.file_listbox.configure(state="normal")
        self.file_listbox.delete("1.0", "end")

        if not self.selected_files:
            self.file_listbox.insert("1.0", "Henüz dosya eklenmedi...\nYukarıdaki butonlarla görsel veya video ekleyebilirsiniz.")
            self.file_count_lbl.configure(text="0 dosya seçildi")
        else:
            lines = []
            for idx, p in enumerate(self.selected_files, 1):
                name = os.path.basename(p)
                ext = os.path.splitext(name)[1].lower()
                icon = "🖼️" if ext in IMAGE_EXTENSIONS else "🎬"
                try:
                    size_mb = os.path.getsize(p) / (1024 * 1024)
                    lines.append(f"[{idx:02d}] {icon} {name} ({size_mb:.2f} MB)")
                except Exception:
                    lines.append(f"[{idx:02d}] {icon} {name}")
            self.file_listbox.insert("1.0", "\n".join(lines))
            self.file_count_lbl.configure(text=f"{len(self.selected_files)} medya dosyası seçildi")

        self.file_listbox.configure(state="disabled")

    def _map_preset(self, val):
        if "4:5" in val:
            return "portrait_4_5"
        elif "9:16" in val:
            return "story_reels_9_16"
        elif "1:1" in val:
            return "square_1_1"
        elif "1.91:1" in val:
            return "landscape_1_91"
        return "original_keep"

    def _map_fit(self, val):
        if "Bulanık" in val:
            return "blur_bg"
        elif "Kırp" in val:
            return "crop_fill"
        elif "Beyaz" in val:
            return "white_border"
        return "black_border"

    def _map_sharpen(self, val):
        if "Hafif" in val:
            return "light"
        elif "Güçlü" in val:
            return "strong"
        elif "Kapalı" in val:
            return "none"
        return "medium"

    def _map_quality(self, val):
        if "%92" in val:
            return 92
        elif "%82" in val:
            return 82
        return 88

    def start_processing(self):
        if self.is_processing:
            return
        if not self.selected_files:
            messagebox.showwarning("Dosya Seçilmedi", "Lütfen önce optimize edilecek görsel veya videoları ekleyin.")
            return

        self.is_processing = True
        self.start_btn.configure(state="disabled", text="⏳ Optimize Ediliyor...")
        self.progress_bar.set(0)

        # Run background thread
        thread = threading.Thread(target=self._process_worker, daemon=True)
        thread.start()

    def _process_worker(self):
        preset = self._map_preset(self.preset_var.get())
        fit = self._map_fit(self.fit_var.get())
        sharpen = self._map_sharpen(self.sharpen_var.get())
        quality = self._map_quality(self.quality_var.get())

        total = len(self.selected_files)
        success_count = 0
        last_output_dir = None

        for idx, file_path in enumerate(self.selected_files):
            fname = os.path.basename(file_path)
            ext = os.path.splitext(fname)[1].lower()

            def update_status(step_pct, step_text):
                overall = (idx + (step_pct / 100)) / total
                self.root.after(0, lambda: self.progress_bar.set(overall))
                self.root.after(0, lambda: self.status_lbl.configure(
                    text=f"[{idx+1}/{total}] {fname} -> {step_text}"
                ))

            try:
                if ext in IMAGE_EXTENSIONS:
                    out = optimize_image(
                        file_path,
                        target_preset=preset,
                        fit_mode=fit,
                        sharpen_level=sharpen,
                        quality=quality,
                        progress_callback=update_status
                    )
                    last_output_dir = os.path.dirname(out)
                    success_count += 1
                elif ext in VIDEO_EXTENSIONS:
                    out = optimize_video(
                        file_path,
                        target_preset=preset,
                        fit_mode=fit,
                        quality=quality,
                        progress_callback=update_status
                    )
                    last_output_dir = os.path.dirname(out)
                    success_count += 1
                else:
                    # Unsupported extension
                    pass
            except Exception as e:
                err_msg = str(e)
                self.root.after(0, lambda: self.status_lbl.configure(
                    text=f"Hata ({fname}): {err_msg}"
                ))

        self.root.after(0, lambda: self.progress_bar.set(1.0))
        self.root.after(0, lambda: self.status_lbl.configure(
            text=f"🎉 Tamamlandı! {success_count}/{total} medya başarıyla optimize edildi."
        ))
        self.root.after(0, lambda: self.start_btn.configure(state="normal", text="🚀 OPTİMİZE ET VE KAYDET"))
        self.is_processing = False

        # Open output folder if selected
        if self.open_folder_var.get() and last_output_dir and os.path.exists(last_output_dir):
            try:
                os.startfile(last_output_dir)
            except Exception:
                pass

        self.root.after(0, lambda: messagebox.showinfo(
            "İşlem Tamamlandı",
            f"{success_count} adet medya Instagram için en yüksek kalitede optimize edildi ve '_insta' uzantısıyla kaydedildi."
        ))

def main():
    if HAS_CTK:
        root = ctk.CTk()
    else:
        root = tk.Tk()
    app = InstagramOptimizerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
