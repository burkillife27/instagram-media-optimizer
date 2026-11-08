import os
import sys
import subprocess
from PIL import Image, ImageOps, ImageFilter

def get_ffmpeg_path():
    """Locate ffmpeg binary: either bundled, in PATH, or from imageio_ffmpeg."""
    # Check if bundled with PyInstaller
    if getattr(sys, 'frozen', False):
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        candidate = os.path.join(base_dir, "ffmpeg.exe")
        if os.path.exists(candidate):
            return candidate

    # Check imageio_ffmpeg
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass

    # Fallback to system PATH
    return "ffmpeg"

def generate_output_path(input_path, suffix="_insta", new_extension=None):
    """
    Generates a non-conflicting output filename like:
    photo.jpg -> photo_insta.jpg
    If photo_insta.jpg exists -> photo_insta_1.jpg, etc.
    """
    directory, filename = os.path.split(input_path)
    base_name, ext = os.path.splitext(filename)
    if new_extension:
        ext = new_extension

    candidate = os.path.join(directory, f"{base_name}{suffix}{ext}")
    counter = 1
    while os.path.exists(candidate):
        candidate = os.path.join(directory, f"{base_name}{suffix}_{counter}{ext}")
        counter += 1
    return candidate

def apply_smart_sharpen(img, strength="medium"):
    """
    Applies fine unsharp masking to counteract downsampling softness
    without generating visible artifacts or noise halos.
    """
    if strength == "none":
        return img
    elif strength == "light":
        # Radius 1.0, 45% amount, threshold 3
        return img.filter(ImageFilter.UnsharpMask(radius=1.0, percent=45, threshold=3))
    elif strength == "strong":
        # Radius 1.5, 90% amount, threshold 2
        return img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=90, threshold=2))
    else:  # "medium" (Default Recommended)
        # Radius 1.2, 65% amount, threshold 2
        return img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=65, threshold=2))

def optimize_image(
    input_path,
    output_path=None,
    target_preset="portrait_4_5",
    fit_mode="blur_bg",
    sharpen_level="medium",
    quality=88,
    progress_callback=None
):
    """
    Optimizes a photo for Instagram:
    - Target resolutions:
        portrait_4_5: 1080x1350
        square_1_1: 1080x1080
        story_reels_9_16: 1080x1920
        landscape_1_91: 1080x566
        original_keep: max width 1080
    - Proper sRGB conversion
    - High-quality Lanczos resampling
    - Unsharp mask for crispness
    - Optimal chroma subsampling (4:4:4) & progressive JPEG
    """
    if progress_callback:
        progress_callback(10, "Resim açılıyor...")

    with Image.open(input_path) as img:
        # Correct orientation from EXIF tags
        img = ImageOps.exif_transpose(img)

        # Ensure RGB color mode (convert CMYK, P, RGBA, etc. to clean sRGB)
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            # Convert alpha to white background
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        orig_w, orig_h = img.size

        # Resolve target dimensions
        presets = {
            "portrait_4_5": (1080, 1350),
            "square_1_1": (1080, 1080),
            "story_reels_9_16": (1080, 1920),
            "landscape_1_91": (1080, 566),
        }

        if progress_callback:
            progress_callback(30, "Boyutlandırılıyor...")

        if target_preset == "original_keep":
            # Just ensure max width is 1080px (Instagram's standard cap)
            if orig_w > 1080:
                new_w = 1080
                new_h = int(round(orig_h * (1080 / orig_w)))
                processed = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            else:
                processed = img.copy()
        else:
            target_w, target_h = presets.get(target_preset, (1080, 1350))
            target_ratio = target_w / target_h
            current_ratio = orig_w / orig_h

            if fit_mode == "crop_fill":
                # Crop to fill exact aspect ratio, then resize
                if current_ratio > target_ratio:
                    # Image is wider: crop sides
                    crop_w = int(round(orig_h * target_ratio))
                    crop_x = (orig_w - crop_w) // 2
                    box = (crop_x, 0, crop_x + crop_w, orig_h)
                else:
                    # Image is taller: crop top/bottom
                    crop_h = int(round(orig_w / target_ratio))
                    crop_y = (orig_h - crop_h) // 2
                    box = (0, crop_y, orig_w, crop_y + crop_h)

                cropped = img.crop(box)
                processed = cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)

            elif fit_mode == "blur_bg":
                # Create blurred background from the image, overlay crisp fit image
                # 1. Resize background to cover target completely, then heavy blur
                bg_ratio = max(target_w / orig_w, target_h / orig_h)
                bg_w = int(round(orig_w * bg_ratio))
                bg_h = int(round(orig_h * bg_ratio))
                bg = img.resize((bg_w, bg_h), Image.Resampling.BILINEAR)
                
                # Center crop background to target size
                crop_x = (bg_w - target_w) // 2
                crop_y = (bg_h - target_h) // 2
                bg = bg.crop((crop_x, crop_y, crop_x + target_w, crop_y + target_h))
                # Heavy Gaussian Blur & darken slightly for aesthetic depth
                bg = bg.filter(ImageFilter.GaussianBlur(radius=35))
                # Darken overlay slightly so foreground pops
                darkener = Image.new("RGB", (target_w, target_h), (0, 0, 0))
                bg = Image.blend(bg, darkener, 0.25)

                # 2. Resize original image to fit within target
                fg_ratio = min(target_w / orig_w, target_h / orig_h)
                fg_w = int(round(orig_w * fg_ratio))
                fg_h = int(round(orig_h * fg_ratio))
                fg = img.resize((fg_w, fg_h), Image.Resampling.LANCZOS)

                # 3. Paste fg centered onto bg
                pos_x = (target_w - fg_w) // 2
                pos_y = (target_h - fg_h) // 2
                bg.paste(fg, (pos_x, pos_y))
                processed = bg

            elif fit_mode == "black_border" or fit_mode == "white_border":
                bg_color = (0, 0, 0) if fit_mode == "black_border" else (255, 255, 255)
                canvas = Image.new("RGB", (target_w, target_h), bg_color)
                
                fg_ratio = min(target_w / orig_w, target_h / orig_h)
                fg_w = int(round(orig_w * fg_ratio))
                fg_h = int(round(orig_h * fg_ratio))
                fg = img.resize((fg_w, fg_h), Image.Resampling.LANCZOS)

                pos_x = (target_w - fg_w) // 2
                pos_y = (target_h - fg_h) // 2
                canvas.paste(fg, (pos_x, pos_y))
                processed = canvas
            else:
                # Direct resize
                processed = img.resize((target_w, target_h), Image.Resampling.LANCZOS)

        if progress_callback:
            progress_callback(70, "Netleştirme uygulanıyor...")

        # Apply smart micro-sharpening
        processed = apply_smart_sharpen(processed, strength=sharpen_level)

        if progress_callback:
            progress_callback(85, "Instagram formatında kaydediliyor...")

        # Prepare output path
        if not output_path:
            output_path = generate_output_path(input_path, suffix="_insta", new_extension=".jpg")

        # Save with Instagram sweet-spot settings:
        # quality=88, subsampling=0 (4:4:4 chroma avoids red/blue color fringing), optimize=True
        processed.save(
            output_path,
            "JPEG",
            quality=quality,
            subsampling=0,
            optimize=True,
            progressive=True
        )

        if progress_callback:
            progress_callback(100, "Tamamlandı!")

        return output_path

def optimize_video(
    input_path,
    output_path=None,
    target_preset="story_reels_9_16",
    fit_mode="crop_fill",
    quality=88,
    progress_callback=None
):
    """
    Optimizes a video for Instagram:
    - Codec: H.264 (libx264) High Profile, Level 4.2
    - Pixel format: yuv420p
    - Color Space: BT.709
    - Audio: AAC stereo 192k 44100Hz
    - Bitrate: CRF 19 (High visual fidelity, tight bounds)
    - Faststart: moov atom at beginning
    """
    ffmpeg_exe = get_ffmpeg_path()
    if not ffmpeg_exe:
        raise RuntimeError("FFmpeg bulunamadı!")

    if not output_path:
        output_path = generate_output_path(input_path, suffix="_insta", new_extension=".mp4")

    presets = {
        "portrait_4_5": (1080, 1350),
        "square_1_1": (1080, 1080),
        "story_reels_9_16": (1080, 1920),
        "landscape_1_91": (1080, 566),
    }

    if target_preset == "original_keep":
        # Cap max width to 1080, keep height even
        vf_filter = "scale='min(1080,iw)':-2"
    else:
        tw, th = presets.get(target_preset, (1080, 1920))
        if fit_mode == "crop_fill":
            # Scale so smaller dimension matches, then crop center
            vf_filter = f"scale={tw}:{th}:force_original_aspect_ratio=increase,crop={tw}:{th}"
        elif fit_mode == "black_border":
            vf_filter = f"scale={tw}:{th}:force_original_aspect_ratio=decrease,pad={tw}:{th}:(ow-iw)/2:(oh-ih)/2:black"
        else: # default blur_bg or similar, for video pad with black or fit
            vf_filter = f"scale={tw}:{th}:force_original_aspect_ratio=decrease,pad={tw}:{th}:(ow-iw)/2:(oh-ih)/2:black"

    # Set CRF based on quality setting
    crf = "19" if quality >= 88 else "22"

    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", input_path,
        "-vf", vf_filter,
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", crf,
        "-maxrate", "14M",
        "-bufsize", "28M",
        "-profile:v", "high",
        "-level", "4.2",
        "-pix_fmt", "yuv420p",
        "-colorspace", "bt709",
        "-color_primaries", "bt709",
        "-color_trc", "bt709",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-ac", "2",
        "-movflags", "+faststart",
        output_path
    ]

    if progress_callback:
        progress_callback(20, "Video kodlanıyor (FFmpeg)...")

    # Run FFmpeg without opening popup console
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        startupinfo=startupinfo,
        universal_newlines=True
    )
    _, stderr = process.communicate()

    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg Hatası: {stderr[-500:] if stderr else 'Bilinmeyen hata'}")

    if progress_callback:
        progress_callback(100, "Tamamlandı!")

    return output_path
