import os
import traceback
import subprocess
import shlex
import json
from moviepy import VideoFileClip, concatenate_videoclips, vfx, AudioFileClip, CompositeAudioClip, TextClip, CompositeVideoClip
try:
    from moviepy.audio.fx.all import audio_loop
except ImportError:
    try:
        # Try finding it in other locations
        from moviepy.audio.fx.audio_loop import audio_loop
    except ImportError:
        # Manual implementation if missing
        from moviepy.audio.AudioClip import concatenate_audioclips
        def audio_loop(audioclip, duration=None, n=None):
            if duration is not None:
                n = int(duration / audioclip.duration) + 1
            elif n is None:
                n = 1
            
            # Create a list of copies
            clips = [audioclip] * n
            # Concatenate
            new_clip = concatenate_audioclips(clips)
            
            if duration is not None:
                new_clip = new_clip.subclipped(0, duration)
            return new_clip

# Ensure concatenate_audioclips is available if we used it above, but also for general use
from moviepy.audio.AudioClip import concatenate_audioclips


from proglog import ProgressBarLogger
EXPORT_DIR = "exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

class RenderLogger(ProgressBarLogger):
    def __init__(self, callback=None):
        super().__init__()
        self.prog_notifier = callback
        self.last_message = ""

    def callback_message(self, message):
        self.last_message = message
        if self.prog_notifier:
            self.prog_notifier({"status": "rendering", "message": message})

    def bars_callback(self, bar, attr, value, old_value=None):
        if self.prog_notifier and "total" in self.bars[bar]:
            total = self.bars[bar]["total"]
            if total > 0:
                percentage = (value / total) * 100
                
                # Debug logging
                try:
                    print(f"DEBUG PROGRESS: bar={bar} val={value}/{total} pct={percentage:.1f}", flush=True)
                except:
                    pass

                # Filter: Only report 't' or 'frame_index' as the main progress
                # MoviePy uses 't' or 'frame_index' depending on the logger/writer
                if bar == 't' or bar == 'frame_index':
                    # Map 0-100% of video rendering to 20-100% of total job
                    # (Reserved 20% for setup/overlays/audio)
                    final_pct = 20 + (percentage * 0.8)
                    try:
                        self.prog_notifier({"status": "rendering", "progress": final_pct, "message": self.last_message})
                    except Exception as e:
                        print(f"Error in prog_notifier: {e}")
                elif bar == 'chunk':
                    # Audio rendering
                    pass

    def write_videofile_safe(self, *args, **kwargs):
             pass

def create_motion_text(content, duration=2.0, style='pop', fontsize=70, color='white', font='Arial-Bold', pos=None, resize_func=None, max_width=None):
    """
    Creates a TextClip using a double-layer technique for clean strokes.
    """
    try:
        effective_fontsize = int(fontsize)
        # Moderate stroke width - not too thick to prevent text balloon effect
        # 8% provides good visibility without making text massive
        stroke_w = max(4, int(effective_fontsize * 0.08))
 
        
        # Method 'caption' allows wrapping. 'label' does not.
        # If max_width is provided, use caption.
        method = 'caption' if max_width else 'label'
        
        # 1. Stroke Layer (Background)
        # We start with a base config
        # 1. Stroke Layer (Background)
        # We start with a base config
        # (Definition merged below)

        # Create the Stroke Layer (Black text with thick black stroke)
        # Note: If we just use stroke_width on the main clip, it renders INSIDE.
        # By compositing, we get the 'Outside' stroke effect.
        
        # 1. Use passed font size (already calculated with boost in main loop)
        calc_fontsize = int(fontsize)

        # 2. Layer Generation Helper
        def make_clip(c_color, c_stroke_color, c_stroke_width):
            text_args = {
                'text': content,
                'font_size': calc_fontsize,
                'color': c_color,
                'stroke_color': c_stroke_color,
                'stroke_width': c_stroke_width,
                'method': method
            }
            if max_width: text_args['size'] = (max_width, None)
            
            # Correctly use function argument 'font'
            try: return TextClip(**text_args, font=font)
            except: 
                try: return TextClip(**text_args, font='Arial')
                except: return TextClip(**{k: v for k, v in text_args.items() if k != 'font'})

        # 3. Create Layers
        # A. Shadow Layer (Offset, slightly blurry/transparent look via color)
        txt_shadow = make_clip('black', None, 0)
        
        # B. Stroke Layer (Background Outline)
        txt_stroke = make_clip('black', 'black', stroke_w)
        
        # C. Fill Layer (Foreground)
        # Correctly use function argument 'color'
        txt_fill = make_clip(color, None, 0)

        # 4. Fade Effects
        if style == 'fade':
            # Apply to all layers
            for clip_layer in [txt_shadow, txt_stroke, txt_fill]:
                try: clip_layer.fadein(0.5).fadeout(0.5)
                except: pass

        # 5. Composite & Align
        # We need a canvas big enough for the stroke + shadow
        # Calculations:
        # stroke layer is biggest normally.
        # shadow is offset by pixels.
        
        shadow_off = max(4, int(calc_fontsize * 0.05)) # 5% of font size as shadow offset
        padding = stroke_w + shadow_off + 10 # ample padding
        
        # Dimensions are based on the stroke layer (largest)
        base_w, base_h = txt_stroke.size
        comp_w = base_w + (padding * 2)
        comp_h = base_h + (padding * 2)
        
        # Center the Stroke Layer in the padded composite
        stroke_pos = (padding, padding)
        
        # Center the Fill Layer RELATIVE to the Stroke Layer
        # (Fill is smaller than stroke, so we center it to avoid 'glitchy' offset)
        fill_dx = (txt_stroke.size[0] - txt_fill.size[0]) / 2
        fill_dy = (txt_stroke.size[1] - txt_fill.size[1]) / 2
        fill_pos = (padding + fill_dx, padding + fill_dy)
        
        # Shadow is same as Fill but offset
        shadow_pos = (fill_pos[0] + shadow_off, fill_pos[1] + shadow_off)
        
        # Position the clips
        ts = txt_stroke.with_position(stroke_pos)
        tf = txt_fill.with_position(fill_pos)
        tshadow = txt_shadow.with_position(shadow_pos)
        
        # Order: Shadow -> Stroke -> Fill
        txt = CompositeVideoClip(
            [tshadow, ts, tf], 
            size=(comp_w, comp_h)
        )
            
        txt = txt.with_duration(duration)
        
        # Positioning Logic - Only apply style-based positioning if no custom pos provided
        # Custom positioning will be applied AFTER creation by the caller
        if pos is None:
            # Apply style-based defaults only when no custom position
            if style == 'slide_up':
                txt = txt.with_position(('center', 0.8), relative=True) 
            elif style == 'fade':
                txt = txt.with_position('center')
                # Fade effects already applied above
            elif style == 'typewriter':
                txt = txt.with_position(('left', 'bottom'))
            else:
                txt = txt.with_position('center')
        # If pos is provided, don't set position here - let caller handle it
            
        return txt
    except Exception as e:
        print(f"❌ Error creating TextClip (Final): {e}")
        traceback.print_exc()
        return None



def apply_grading(clip, grading_settings):
    """
    Applies color grading using raw NumPy manipulation for guaranteed results.
    """
    import numpy as np

    # 1. Parse Settings
    try:
        temp = float(grading_settings.get('temperature', 5600))
        exp = float(grading_settings.get('exposure', 0.0))
        con = float(grading_settings.get('contrast', 0))
        sat = float(grading_settings.get('saturation', 100))
        filter_name = grading_settings.get('filterSuggestion', 'None')
    except:
        return clip

    # Check if we need to do anything (optimization)
    if temp == 5600 and exp == 0 and con == 0 and sat == 100 and filter_name == 'None':
        return clip

    print(f"🎨 NumPy Grading -> T:{temp} E:{exp} C:{con} S:{sat} F:{filter_name}", flush=True)

    def filter_frame(image):
        # Image is a numpy array [H, W, 3] uint8
        img = image.astype(float)

        # 1. Temperature (Simplified)
        if temp != 5600:
            val = (temp - 5600) / 5000.0 # -0.8 to +0.8
            r_gain = 1 + (val * 0.2)
            b_gain = 1 - (val * 0.2)
            img[:, :, 0] *= r_gain
            img[:, :, 2] *= b_gain

        # 2. Exposure
        if exp != 0:
            factor = 2 ** exp
            img *= factor

        # 3. Contrast
        if con != 0:
            factor = 1 + (con / 100.0)
            # Pivot around 128 (midpoint)
            img = (img - 128.0) * factor + 128.0

        # 4. Saturation (Simple RGB separation)
        if sat != 100:
             factor = sat / 100.0
             # Gray is approx magnitude of RGB
             # simple avg for speed 
             gray = np.mean(img, axis=2, keepdims=True)
             img = gray + (img - gray) * factor

        # 5. Simple Filter Presets (Overwrites)
        # 5. Advanced Filter Presets
        if filter_name == "Cinematic":
             # High contrast, slight desaturation, moody
             img = (img - 128.0) * 1.2 + 128.0
             img *= 0.95
        
        elif filter_name == "Teal & Orange":
             # Shadow -> Teal, Highlight -> Orange
             # Simplified Channel Mixer
             r = img[:, :, 0]
             g = img[:, :, 1]
             b = img[:, :, 2]
             
             # Boost Red in highlights (Orange)
             r = np.where(r > 128, r * 1.2, r * 0.9)
             # Boost Blue in shadows (Teal)
             b = np.where(b < 128, b * 1.2, b * 0.9)
             
             img[:, :, 0] = np.clip(r, 0, 255)
             img[:, :, 2] = np.clip(b, 0, 255)
             
             # Contrast bump
             img = (img - 128.0) * 1.1 + 128.0

        elif filter_name == "Vintage":
             # Sepia-ish
             # R * 1.1, B * 0.9 + Lift Blacks
             img[:, :, 0] *= 1.1 # R
             img[:, :, 2] *= 0.85 # B
             img = (img - 128.0) * 0.9 + 128.0 # Lower contrast
             img += 10 # Lift blacks

        elif filter_name == "Noir":
             # B&W + High Contrast
             gray = np.mean(img, axis=2, keepdims=True)
             img = gray
             img = (img - 128.0) * 1.5 + 128.0
        
        elif filter_name == "Vivid":
             # Boost sat strongly
             gray = np.mean(img, axis=2, keepdims=True)
             img = gray + (img - gray) * 1.5
        
        elif filter_name == "Vivid Warm":
             # Boost sat + Warm temp
             gray = np.mean(img, axis=2, keepdims=True)
             img = gray + (img - gray) * 1.3
             img[:, :, 0] *= 1.1 # R up
             img[:, :, 2] *= 0.9 # B down

        elif filter_name == "Vivid Cool":
             # Boost sat + Cool temp
             gray = np.mean(img, axis=2, keepdims=True)
             img = gray + (img - gray) * 1.3
             img[:, :, 0] *= 0.9 # R down
             img[:, :, 2] *= 1.1 # B up

        elif filter_name == "Dramatic":
             # Desaturated + High Contrast
             gray = np.mean(img, axis=2, keepdims=True)
             img = gray + (img - gray) * 0.8 # Desaturate
             img = (img - 128.0) * 1.4 + 128.0 # High Contrast

        elif filter_name == "Mono" or filter_name == "B&W":
             gray = np.mean(img, axis=2, keepdims=True)
             img = gray 
             
        elif filter_name == "Silvertone":
             # B&W + Brightness push + Contrast
             gray = np.mean(img, axis=2, keepdims=True)
             img = gray
             img = (img - 128.0) * 1.2 + 128.0
             img *= 1.1 # Bright

        # Clip and cast back
        return np.clip(img, 0, 255).astype(np.uint8)

    # Use fl_image if available (standard in MoviePy)
    # If using MoviePy 2.x, it might be renamed, but fl_image usually persists.
    if hasattr(clip, 'fl_image'):
        return clip.fl_image(filter_frame)
    else:
        # Fallback for very new versions if fl_image is gone
        return clip.transform(lambda get_frame, t: filter_frame(get_frame(t)))

import time

import traceback

def render_project(project_data, progress_callback=None):
    """
    1. Reads the instructions from React
    2. Cuts the video
    3. Stitches it together
    4. Exports to MP4
    """
    print("🎬 Starting Render Job...")
    if progress_callback:
        progress_callback({"status": "processing", "progress": 0, "message": "Starting Render Job..."})

    final_clips = []
    
    # We might need to adjust paths if running from root
    # "uploads" folder is likely in root.
    UPLOAD_DIR = "uploads"
    
    try:
        # Extract Global Settings
        # Handle cases where keys might be missing or different casing
        global_settings = project_data.get('globalSettings', {})
        global_grading = global_settings.get('colorGrading', {})
        global_filter = global_settings.get('filterSuggestion', 'None')
        
        # Ensure we have a dict
        if not isinstance(global_grading, dict): global_grading = {}
        
        # Determine clips list (handle 'edl' or 'clips' key)
        clips_list = project_data.get('edl', project_data.get('clips', []))
        total_clips = len(clips_list)
        processed_count = 0

        for i, clip_data in enumerate(clips_list):
            # SKIP clips the user marked as 'Red/Remove'
            # Handle boolean or string "false"
            keep_val = clip_data.get('keep', True)
            if isinstance(keep_val, str) and keep_val.lower() == 'false':
                 keep_val = False
            
            if not keep_val:
                print(f"✂️ Skipping clip {clip_data.get('id')} (keep={keep_val})")
                continue
                
            source_name = clip_data['source']
            if progress_callback:
                progress_callback({
                    "status": "processing", 
                    "progress": (i / total_clips) * 10,  # First 10% is for loading/clipping
                    "message": f"Processing clip {i+1}/{total_clips}"
                })
            
            try:
                # A. Resolve Source Path

                # Priority 0: Absolute Path (Provided by Manual Mode or Direct Link)
                if os.path.isabs(source_name) and os.path.exists(source_name):
                    source_path = source_name
                else:
                    # Priority 1: Uploads folder (Legacy)
                    source_path = os.path.join(UPLOAD_DIR, os.path.basename(source_name))
                
                # Priority 2: Project Specific Folder
                if not os.path.exists(source_path):
                     p_name = project_data.get('name', '')
                     # Try exact name
                     safe_name = "".join(c for c in p_name if c.isalnum() or c in (' ', '_', '-')).strip()
                     project_media_path = os.path.join("projects", safe_name, "source_media", os.path.basename(source_name))
                     
                     if os.path.exists(project_media_path):
                         source_path = project_media_path
                     else:
                         # Try heuristic for Shorts (e.g. "LateShow_Short1" -> "LateShow")
                         parts = safe_name.split('_')
                         if len(parts) > 1:
                             base_name = parts[0]
                             heuristic_path = os.path.join("projects", base_name, "source_media", os.path.basename(source_name))
                             if os.path.exists(heuristic_path):
                                 source_path = heuristic_path
                
                # Priority 3: Absolute Fallback (for testing)
                if not os.path.exists(source_path):
                    abs_fallback = os.path.join("/Users/saieshwarrampelli/Downloads/GravityEdits/source_media", os.path.basename(source_name))
                    if os.path.exists(abs_fallback):
                        source_path = abs_fallback
                    
                    # Heuristic: If source_name has no extension, try adding .mp4 or .mov
                    if not os.path.exists(source_path) and '.' not in source_name:
                        for ext in ['.mp4', '.mov', '.mkv']:
                            test_path = source_path + ext
                            if os.path.exists(test_path):
                                source_path = test_path
                                break

                # Priority 4: Deep Search in ALL valid project folders
                # (Fix for Shorts derived from other projects where path refs might be stale)
                if not os.path.exists(source_path):
                     projects_root = "projects"
                     if os.path.exists(projects_root):
                         for p_dir in os.listdir(projects_root):
                             if p_dir.startswith('.'): continue
                             possible_path = os.path.join(projects_root, p_dir, "source_media", os.path.basename(source_name))
                             if os.path.exists(possible_path):
                                 source_path = possible_path
                                 print(f"   ✅ Found source in sibling project: {source_path}")
                                 break

                if not os.path.exists(source_path):
                     print(f"⚠️ Source file missing: {source_path}")
                     continue

                # A. Load Video
                original_video = VideoFileClip(source_path)
                
                # B. Trim (The "Scissors" Logic)
                # We use the start/end times we saved earlier
                start = float(clip_data.get('start', 0))
                end_val = clip_data.get('end')
                
                # If end is 0 or missing, use duration or video end
                if not end_val or float(end_val) == 0:
                     duration = float(clip_data.get('duration', 0))
                     if duration > 0:
                         end_val = start + duration
                     else:
                         end_val = original_video.duration

                end = float(end_val)
                
                # Safety check: ensure we don't cut past the end of video
                if end > original_video.duration: end = original_video.duration
                if start >= end:
                     print(f"⚠️ Invalid trim for {clip_data['id']}: start {start} >= end {end}")
                     # Try to fix if it's just a small drift, otherwise skip
                     if start < original_video.duration:
                         end = original_video.duration
                     else:
                         continue
                
                cut_clip = original_video.subclipped(start, end)
                
                # C. Apply Color Filter / Grading
                # Merge Global + Clip Grading
                clip_grading = clip_data.get('colorGrading', {})
                if not isinstance(clip_grading, dict): clip_grading = {}
                
                # Start with global
                merged_settings = global_grading.copy()
                # Override with clip specific (if non-zero/default)
                # Actually, usually users want clip grading to ADD to global or REPLACE?
                # For simplicity, we'll let clip-specific values override global provided they exist.
                # Or better: if clip has specific grading, use it.
                if clip_grading:
                    merged_settings.update(clip_grading)
                
                # Pass the named filter too
                merged_settings['filterSuggestion'] = global_filter
                
                cut_clip = apply_grading(cut_clip, merged_settings)

                # D. Aspect Ratio Transformation (Shorts/Portrait)
                # Check for renderMode explicitly
                render_mode = project_data.get('renderMode', 'landscape')
                
                # Heuristic: If name implies short and no mode set? 
                # Better to rely on frontend flag we will add.

                if render_mode == 'portrait':
                     w, h = cut_clip.size
                     target_ratio = 9/16
                     
                     # 1. Center Crop
                     # Calculate target width for current height to match 9:16
                     new_w = int(h * target_ratio)
                     
                     if new_w < w:
                         # Landscape or Square -> Crop width
                         center_x = w / 2
                         x1 = center_x - (new_w / 2)
                         cut_clip = cut_clip.cropped(x1=x1, width=new_w, height=h)
                         
                     # 2. Resize to 1080x1920 (Standard HD Shorts)
                     # Check if resize is needed to avoid unnecessary processing
                     if cut_clip.size != (1080, 1920):
                        cut_clip = cut_clip.resized((1080, 1920))

                final_clips.append(cut_clip)
                
            except Exception as e:
                print(f"⚠️ Error processing clip {clip_data.get('id')}: {e}")
                print(traceback.format_exc()) # CRITICAL: See exactly why it failed

        if not final_clips:
            print("❌ No valid clips to render.")
            if progress_callback:
                progress_callback({"status": "failed", "message": "No valid clips to render (Check logs for details)"})
            return None

        # E. Stitch (Concatenate)
        print(f"🔨 Stitching {len(final_clips)} clips together...")
        if progress_callback:
                progress_callback({"status": "processing", "progress": 10, "message": "Stitching clips..."})
        
        final_video = concatenate_videoclips(final_clips, method="compose")

        # --- HYBRID PIPELINE: PREPARE OVERLAYS ---
        overlays_to_render = []
        overlays_data = project_data.get('overlays', [])

        if overlays_data:
            if progress_callback: progress_callback({"status": "processing", "progress": 12, "message": "Preparing Overlay Data..."})
            print(f"✨ Preparing {len(overlays_data)} text overlays for Hybrid Render...")
            
            vw, vh = final_video.size
            
            for overlay in overlays_data:
                try:
                    content = overlay.get('content', '')
                    start = float(overlay.get('start', 0))
                    dur = float(overlay.get('duration', 2.0))
                    style = overlay.get('style', 'pop')
                    
                    # Properties
                    f_size_pct = overlay.get('fontSize', 4) 
                    t_color = overlay.get('textColor', 'white')
                    font_fam = overlay.get('fontFamily', 'Arial-Bold')
                    
                    # 1. Calculate Font Size (% of video HEIGHT)
                    try:
                        f_norm = float(f_size_pct) if f_size_pct else 0.05
                    except: f_norm = 0.05
                    if f_norm > 1.0: f_norm = f_norm / 100.0
                    
                    # De-normalize and Boost
                    calc_fontsize = int(vh * f_norm * 1.5)
                    if calc_fontsize < 60: calc_fontsize = 60
                    
                    # 2. Coordinates
                    p_x = overlay.get('positionX')
                    p_y = overlay.get('positionY')
                    try:
                        pos_x = float(p_x) if p_x is not None else 0.5
                        pos_y = float(p_y) if p_y is not None else 0.8
                    except: pos_x, pos_y = 0.5, 0.8
                    if pos_x > 1.0: pos_x = pos_x / 100.0
                    if pos_y > 1.0: pos_y = pos_y / 100.0
                    
                    # 3. Text Wrapping Width
                    safe_text_width = None
                    if len(content) > 20: safe_text_width = int(vw * 0.85)

                    # Store for Asset Generation Phase
                    overlays_to_render.append({
                        "content": content,
                        "start": start,
                        "duration": dur,
                        "style": style,
                        "fontsize": calc_fontsize,
                        "color": t_color,
                        "font": font_fam,
                        "max_width": safe_text_width,
                        "pos_x_norm": pos_x,
                        "pos_y_norm": pos_y
                    })

                except Exception as e:
                    print(f"❌ Failed to prepare overlay {overlay}: {e}")

        # G. Apply Audio Mixing (Background Music & Secondary Tracks)
        audio_layers = []
        if final_video.audio:
            audio_layers.append(final_video.audio)
        
        # 1. Background Score
        bg_music_config = project_data.get('bgMusic')
        if bg_music_config and bg_music_config.get('source'):
            try:
                music_file = bg_music_config['source']
                music_path = os.path.join(UPLOAD_DIR, music_file)
                # ... (Path resolution logic omitted for brevity, assume standard flows or copy if needed) ...
                # Re-implementing path search to ensure robusteness
                if not os.path.exists(music_path):
                     p_name = project_data.get('name')
                     if p_name:
                         safe_name = "".join(c for c in p_name if c.isalnum() or c in (' ', '_', '-')).strip()
                         alt = os.path.join("projects", safe_name, "source_media", music_file)
                         if os.path.exists(alt): music_path = alt

                if os.path.exists(music_path):
                    bg_music = AudioFileClip(music_path)
                    
                    track_volumes = project_data.get('trackVolumes', {})
                    vol = float(track_volumes.get('music', bg_music_config.get('volume', 0.5)))
                    bg_music = bg_music.multiply_volume(vol)
                    
                    bg_start = float(bg_music_config.get('start', 0))
                    bg_user_duration = bg_music_config.get('duration')
                    
                    video_duration = final_video.duration
                    
                    if bg_user_duration:
                        dur_val = float(bg_user_duration)
                        if bg_music.duration < dur_val: bg_music = audio_loop(bg_music, duration=dur_val)
                        else: bg_music = bg_music.subclipped(0, dur_val)
                    else:
                        rem = max(0, video_duration - bg_start)
                        if bg_music.duration < rem: bg_music = audio_loop(bg_music, duration=rem)
                        else: bg_music = bg_music.subclipped(0, rem)

                    bg_music = bg_music.with_start(bg_start)
                    audio_layers.append(bg_music)
            except Exception as e:
                print(f"⚠️ BG Music Error: {e}")

        # 2. Secondary Audio Clips
        secondary_clips = project_data.get('audioClips', [])
        for clip_data in secondary_clips:
            try:
                sfx_file = clip_data.get('source')
                start_time = float(clip_data.get('start', 0))
                # Path resolution
                sfx_path = os.path.join(UPLOAD_DIR, sfx_file)
                if not os.path.exists(sfx_path):
                     p_name = project_data.get('name')
                     if p_name:
                         safe_name = "".join(c for c in p_name if c.isalnum() or c in (' ', '_', '-')).strip()
                         alt = os.path.join("projects", safe_name, "source_media", sfx_file)
                         if os.path.exists(alt): sfx_path = alt

                if os.path.exists(sfx_path):
                    sfx_clip = AudioFileClip(sfx_path)
                    vol = float(project_data.get('trackVolumes', {}).get(f"a{clip_data.get('track',2)}", 1.0))
                    sfx_clip = sfx_clip.multiply_volume(vol)
                    
                    user_dur = clip_data.get('duration')
                    target_dur = float(user_dur) if user_dur else sfx_clip.duration
                    if target_dur < sfx_clip.duration: sfx_clip = sfx_clip.subclipped(0, target_dur)
                    sfx_clip = sfx_clip.with_start(start_time)
                    audio_layers.append(sfx_clip)
            except Exception as e: print(f"Audio Clip Error: {e}")

        # H. Final Audio Mixing
        if len(audio_layers) > 0:
             final_audio = CompositeAudioClip(audio_layers)
             final_video = final_video.with_audio(final_audio)

        # --- I. HYBRID EXPORT ---
        timestamp = int(time.time())
        output_filename = f"{project_data.get('name', 'video')}_final_{timestamp}.mp4"
        output_path = os.path.join(EXPORT_DIR, output_filename)
        
        # Temp paths
        temp_base_path = os.path.join(EXPORT_DIR, f"temp_base_{timestamp}.mp4")
        temp_assets = []

        try:
            # 1. Render Base Video (Low Memory safe)
            if progress_callback: progress_callback({"status": "rendering", "progress": 20, "message": "Rendering Base Video Layer..."})
            print("💾 Rendering Base Video Layer...")
            final_video.write_videofile(
                temp_base_path, 
                fps=24, 
                preset="ultrafast", 
                codec="libx264", 
                audio_codec="aac", 
                threads=1,
                logger=None # Silence MoviePy to keep logs clean
            )

            # 2. Render Overlay Assets
            if progress_callback: progress_callback({"status": "rendering", "progress": 50, "message": "Generating Text Assets..."})
            print("🎨 Generating Text Assets (Hybrid Mode)...")
            
            ffmpeg_inputs = ['-i', temp_base_path]
            filter_complex = []
            
            # Map [0:v] is base
            # Overlays start at index 1
            
            for i, ov in enumerate(overlays_to_render):
                # asset path
                asset_path = os.path.join(EXPORT_DIR, f"temp_ov_{timestamp}_{i}.mov")
                
                # Generate Clip
                txt_clip = create_motion_text(
                    ov['content'],
                    duration=ov['duration'],
                    style=ov['style'],
                    fontsize=ov['fontsize'],
                    color=ov['color'],
                    font=ov['font'],
                    max_width=ov['max_width']
                )
                
                if txt_clip:
                    # Write Transparent Video Asset
                    txt_clip.write_videofile(
                        asset_path, 
                        fps=24, 
                        codec="png", # Supports Alpha
                        audio=False, 
                        threads=2,
                        logger=None
                    )
                    temp_assets.append(asset_path)
                    
                    # Add to Inputs
                    ffmpeg_inputs.extend(['-i', asset_path])
                    input_idx = i + 1
                    
                    # Calculate Pixel Position for FFmpeg
                    # txt_clip size
                    tw, th = txt_clip.size
                    
                    # De-normalize Center
                    center_x = ov['pos_x_norm'] * vw
                    center_y = ov['pos_y_norm'] * vh
                    
                    # Top-Left for FFmpeg
                    tl_x = int(center_x - (tw / 2))
                    tl_y = int(center_y - (th / 2))
                    
                    # Clamp
                    tl_x = max(0, min(tl_x, vw - tw))
                    tl_y = max(0, min(tl_y, vh - th))
                    
                    # Filter Chain
                    # Chain: [prev_layer][new_layer]overlay=...[next_layer]
                    prev_label = f"{input_idx-1}:v" if i == 0 else f"v{i}" # 0:v is base
                    if i == 0: prev_label = "0:v"
                    
                    next_label = f"v{i+1}"
                    
                    # enable='between(t,start,end)'
                    enable_expr = f"enable='between(t,{ov['start']},{ov['start']+ov['duration']})'"
                    
                    cmd = f"[{prev_label}][{input_idx}:v]overlay=x={tl_x}:y={tl_y}:{enable_expr}"
                    if i < len(overlays_to_render) - 1:
                        cmd += f"[{next_label}]"
                    
                    filter_complex.append(cmd)
            
            # 3. Stitch with FFmpeg
            if progress_callback: progress_callback({"status": "rendering", "progress": 80, "message": "Stitching Final Video..."})
            print("🧵 Stitching Final Video with FFmpeg...")

            if not filter_complex:
                # No overlays, just rename base to output
                os.rename(temp_base_path, output_path)
            else:
                # Build Full Command
                full_filter = ";".join(filter_complex)
                
                cmd = [
                    "ffmpeg", "-y",
                    *ffmpeg_inputs,
                    "-filter_complex", full_filter,
                    "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                    "-c:a", "copy", # Copy audio from Base (input 0)
                    "-map", f"{len(overlays_to_render) if len(overlays_to_render) > 0 else 0}:v" if len(overlays_to_render) == 0 else (f"[v{len(overlays_to_render)}]" if len(overlays_to_render) > 0 else "0:v"),
                    "-map", "0:a", # Map audio from base
                    output_path
                ]
                
                # Fix map logic: The last overlay output is [vN]
                last_label = f"[v{len(overlays_to_render)}]"
                
                # Command Construction Refined
                cmd_args = ["ffmpeg", "-y"]
                cmd_args.extend(ffmpeg_inputs)
                cmd_args.extend(["-filter_complex", full_filter])
                cmd_args.extend([
                    "-map", last_label, 
                    "-map", "0:a", 
                    "-c:v", "libx264", "-preset", "ultrafast",
                    "-c:a", "copy",
                    output_path
                ])
                
                print(f"   Run: {' '.join(cmd_args)}")
                subprocess.run(cmd_args, check=True)

        finally:
            # Cleanup
            print("🧹 Cleaning up temp files...")
            if os.path.exists(temp_base_path): os.remove(temp_base_path)
            for p in temp_assets:
                if os.path.exists(p): os.remove(p)

        print(f"✅ Video Saved: {output_path}")
        if progress_callback:
            progress_callback({"status": "completed", "progress": 100, "message": "Render Complete", "url": f"/exports/{output_filename}"})
        
        # --- NEW: Generate Subtitles ---
        try:
            from . import subtitle_generator
            srt_filename = output_filename.replace('.mp4', '.srt')
            srt_path = os.path.join(EXPORT_DIR, srt_filename)
            subtitle_generator.generate_srt(project_data, srt_path)
            print(f"📝 Subtitles saved to: {srt_path}")
        except Exception as e:
            print(f"⚠️ Subtitle generation failed: {e}")
        # -------------------------------
        
        # Clean up
        for c in final_clips:
            c.close()
            
        return output_path
        
    except Exception as e:
        print(f"Rendering error: {e}")
        if progress_callback:
            progress_callback({"status": "failed", "message": str(e)})
        raise e
