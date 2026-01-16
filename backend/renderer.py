import os
import traceback
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

        # --- NEW: Process Overlays ---
        overlays = project_data.get('overlays', [])
        if overlays:
            if progress_callback: progress_callback({"status": "processing", "progress": 12, "message": "Generating Text Overlays..."})
            print(f"✨ Adding {len(overlays)} text overlays...")
            print(f"📐 Video resolution: {final_video.size[0]}x{final_video.size[1]}")
            overlay_clips = [final_video] # Base layer
            
            # Get video dimensions for calculations
            vw, vh = final_video.size
            print(f"🎬 Processing overlays for {vw}x{vh} video")
            
            for overlay in overlays:
                try:
                    content = overlay.get('content', '')
                    start = float(overlay.get('start', 0))
                    dur = float(overlay.get('duration', 2.0))
                    style = overlay.get('style', 'pop')
                    
                    # New properties from Frontend
                    # fontSize is in 'percentage of width' (cqw equivalent)
                    f_size_pct = overlay.get('fontSize', 4) 
                    
                    # Position is % 0-100
                    p_x = overlay.get('positionX')
                    p_y = overlay.get('positionY')
                    t_color = overlay.get('textColor', 'white')
                    font_fam = overlay.get('fontFamily', 'Arial-Bold')
                    
                    # ========================================
                    # NORMALIZED COORDINATE SYSTEM (0.0 to 1.0)
                    # ========================================
                    # Frontend sends:
                    #   - fontSize: 0.0-1.0 (% of video HEIGHT)
                    #   - positionX: 0.0-1.0 (center of text, 0=left, 1=right)
                    #   - positionY: 0.0-1.0 (center of text, 0=top, 1=bottom)
                    
                    # 1. Calculate Font Size (% of video HEIGHT)
                    try:
                        f_norm = float(f_size_pct) if f_size_pct else 0.05
                    except: 
                        f_norm = 0.05  # Default 5% of height
                    
                    # OLD DATA MIGRATION: If value > 1, assume it's old 0-100 format
                    if f_norm > 1.0:
                        f_norm = f_norm / 100.0
                    
                    # De-normalize: multiply by video HEIGHT
                    # VISUAL CORRECTION: Added 1.5x multiplier because "5% height" in 
                    # standard video rendering looks smaller than "5vh" in CSS due to pixel density/weight.
                    # This ensures the "Bold Social Media" look.
                    calc_fontsize = int(vh * f_norm * 1.5)
                    
                    # Minimum size for readability
                    if calc_fontsize < 60: calc_fontsize = 60
                    
                    print(f"  📝 Overlay '{content}': fontSize={f_norm:.3f} (norm) * 2.0 -> {calc_fontsize}px, color={t_color}")

                    # 2. Parse Position (normalized 0.0 to 1.0)
                    try:
                        pos_x = float(p_x) if p_x is not None else 0.5
                        pos_y = float(p_y) if p_y is not None else 0.8
                    except:
                        pos_x, pos_y = 0.5, 0.8  # Default center-bottom
                    
                    # OLD DATA MIGRATION: If values > 1, assume old 0-100 format
                    if pos_x > 1.0:
                        pos_x = pos_x / 100.0
                    if pos_y > 1.0:
                        pos_y = pos_y / 100.0
                    
                    print(f"    ↳ Position: ({pos_x:.3f}, {pos_y:.3f}) normalized")
                    
                    # 3. Text wrapping
                    # Only wrap for LONG text. Short text (like "Hey") should be single line
                    safe_text_width = None
                    if len(content) > 20:  # Only wrap long text
                        safe_text_width = int(vw * 0.85)
                    
                    # 3. Create Clip - DON'T pass custom position to function
                    # Let it apply style-based defaults, we'll override with custom position after
                    txt = create_motion_text(
                        content, 
                        duration=dur, 
                        style=style, 
                        fontsize=calc_fontsize, 
                        color=t_color, 
                        font=font_fam,
                        pos=None,  # Always None - we handle positioning below
                        max_width=safe_text_width
                    )
                    
                    if txt:
                        txt = txt.with_start(start)
                        
                        # 4. DE-NORMALIZE Position: Convert 0-1 to actual pixels
                        # The position represents where the CENTER of the text should be
                        tw, th = txt.size
                        
                        # De-normalize: multiply by video dimensions
                        center_x = pos_x * vw
                        center_y = pos_y * vh
                        
                        # Calculate Top-Left coordinate (anchoring at CENTER)
                        tl_x = center_x - (tw / 2)
                        tl_y = center_y - (th / 2)
                        
                        # Clamp to video bounds
                        tl_x_original = tl_x
                        tl_y_original = tl_y
                        tl_x = max(0, min(tl_x, vw - tw))
                        tl_y = max(0, min(tl_y, vh - th))
                        
                        txt = txt.with_position((tl_x, tl_y))
                        
                        # Log with warning if position was clamped
                        if tl_x != tl_x_original or tl_y != tl_y_original:
                            print(f"    ⚠️  Position clamped to fit {vw}x{vh} video")
                        print(f"    ↳ Text size: {tw}x{th}, center: ({center_x:.0f}, {center_y:.0f}) -> top-left: ({tl_x:.0f}, {tl_y:.0f})")
                        
                        overlay_clips.append(txt)
                        print(f"  ✅ Added overlay at {start}s for {dur}s")
                except Exception as e:
                    print(f"❌ Failed to add overlay {overlay}: {e}")
                    traceback.print_exc()
            
            if len(overlay_clips) > 1:
                # CompositeVideoClip allows layering
                final_video = CompositeVideoClip(overlay_clips)
        # -----------------------------

        # G. Apply Audio Mixing (Background Music & Secondary Tracks)
        audio_layers = []
        if final_video.audio:
            audio_layers.append(final_video.audio)
        
        # 1. Background Score (Legacy & Migrated)
        bg_music_config = project_data.get('bgMusic')
        if bg_music_config and bg_music_config.get('source'):
            try:
                music_file = bg_music_config['source']
                print(f"🎵 Processing background music: {music_file}")
                print(f"   Config: start={bg_music_config.get('start', 0)}, volume={bg_music_config.get('volume', 0.5)}, duration={bg_music_config.get('duration', 'auto')}")
                
                # Search paths
                music_path = os.path.join(UPLOAD_DIR, music_file)
                if not os.path.exists(music_path):
                     p_name = project_data.get('name')
                     if p_name:
                         safe_name = "".join(c for c in p_name if c.isalnum() or c in (' ', '_', '-')).strip()
                         music_path_alt = os.path.join("projects", safe_name, "source_media", music_file)
                         if os.path.exists(music_path_alt):
                             music_path = music_path_alt
                             print(f"   Found at: {music_path}")
                
                if os.path.exists(music_path):
                    print(f"   ✅ Loading audio from: {music_path}")
                    bg_music = AudioFileClip(music_path)
                    print(f"   ✅ Audio loaded: duration={bg_music.duration:.2f}s, fps={bg_music.fps}")
                    
                    # Handle volume - Check trackVolumes first, then bgMusic.volume
                    track_volumes = project_data.get('trackVolumes', {})
                    if 'music' in track_volumes:
                        vol = float(track_volumes['music'])
                        print(f"   🔊 Using trackVolumes.music: {vol}")
                    else:
                        vol = float(bg_music_config.get('volume', 0.5))
                        print(f"   🔊 Using bgMusic.volume: {vol}")
                    
                    bg_music = bg_music.multiply_volume(vol)
                    
                    # Handle Start Time & Duration
                    # If this is the "Legacy" bgMusic track that is now draggable:
                    bg_start = float(bg_music_config.get('start', 0))
                    bg_user_duration = bg_music_config.get('duration')
                    
                    video_duration = final_video.duration

                    # If duration provided (it was split/trimmed), use it
                    if bg_user_duration:
                        dur = float(bg_user_duration)
                        # Trim source to this duration? Or Loop until this duration?
                        # Usually "duration" in timeline means "length of clip".
                        # If source is shorter, loop. If source is longer, cut.
                        if bg_music.duration < dur:
                             bg_music = audio_loop(bg_music, duration=dur)
                        else:
                             bg_music = bg_music.subclipped(0, dur)
                    else:
                        # Legacy Loop Mode: Fill entire video
                        # Calculate remaining time from start
                        remaining_dur = max(0, video_duration - bg_start)
                        if bg_music.duration < remaining_dur:
                            bg_music = audio_loop(bg_music, duration=remaining_dur)
                        else:
                            bg_music = bg_music.subclipped(0, remaining_dur)

                    bg_music = bg_music.with_start(bg_start)
                    
                    audio_layers.append(bg_music)
                    print(f"   ✅ Background music added to audio layers (start={bg_start}s, volume={vol})")
                else:
                    print(f"   ❌ Music file not found at: {music_path}")
            except Exception as e:
                print(f"⚠️ Failed to add background music: {e}")
                traceback.print_exc()
        elif bg_music_config:
            print(f"⚠️ bgMusic config exists but no source: {bg_music_config}")
        else:
            print(f"ℹ️  No background music configured")

        # 2. Secondary Audio Clips (A2 / SFX / Split Music)
        secondary_clips = project_data.get('audioClips', [])
        if secondary_clips:
            print(f"🔊 Adding {len(secondary_clips)} secondary audio clips...")
            for clip_data in secondary_clips:
                try:
                    sfx_file = clip_data.get('source')
                    start_time = float(clip_data.get('start', 0))
                    user_duration = clip_data.get('duration')
                    
                    # Check paths
                    sfx_path = os.path.join(UPLOAD_DIR, sfx_file)
                    if not os.path.exists(sfx_path):
                         p_name = project_data.get('name')
                         if p_name:
                             safe_name = "".join(c for c in p_name if c.isalnum() or c in (' ', '_', '-')).strip()
                             sfx_path_alt = os.path.join("projects", safe_name, "source_media", sfx_file)
                             if os.path.exists(sfx_path_alt):
                                 sfx_path = sfx_path_alt
                    
                    if os.path.exists(sfx_path):
                        sfx_clip = AudioFileClip(sfx_path)
                        
                        # Handle Duration (Cutting)
                        # If frontend created a "Part 2" clip, it usually expects the Playback to resume from the split point.
                        # Wait, my frontend logic: "part2 = {start: ..., duration: ...}".
                        # BUT it didn't specify "media_start" (start point in source file)!
                        # Standard EDL usually has `timeline_start` AND `media_start`.
                        # Currently, my `AudioClip` model in `types.ts` DOES NOT HAVE `mediaStart` or `inPoint`.
                        # It is effectively assuming every clip starts from 0:00 of the source file.
                        # THIS IS A BUG FOR SPLIT CLIPS!
                        
                        # FIX LOGIC: When splitting Audio, we must track where in the source file we are.
                        # BUT `types.ts` AudioClip interface:
                        # export interface AudioClip { id, source, start, duration, track }
                        # It lacks `offset` or `trimStart`.
                        # Meaning separate clips will ALL restart the music from the beginning (0:00).
                        
                        # I cannot fix this in renderer alone if the data isn't there.
                        # However, for now, let's assume standard behavior: Clip starts at 0.
                        # I will add `subclip(0, duration)` to respect the cut length.
                        # But Part 2 will restart the song. The user will notice this.
                        
                        target_dur = float(user_duration) if user_duration else sfx_clip.duration
                        if target_dur < sfx_clip.duration:
                             sfx_clip = sfx_clip.subclipped(0, target_dur)
                        
                        sfx_clip = sfx_clip.with_start(start_time)
                        
                        # Clip if goes beyond video?
                        # if start_time + sfx_clip.duration > final_video.duration:
                        #    sfx_clip = sfx_clip.subclip(0, final_video.duration - start_time)
                    
                        audio_layers.append(sfx_clip)
                except Exception as e:
                    print(f"⚠️ Failed to add secondary clip {clip_data}: {e}")

        # H. Final Audio Mixing
        if progress_callback: progress_callback({"status": "processing", "progress": 18, "message": "Mixing Audio Tracks..."})
        print(f"🎚️  Mixing {len(audio_layers)} audio layers...")
        if len(audio_layers) > 0:
             print(f"   Audio layers: {[type(layer).__name__ for layer in audio_layers]}")
             final_audio = CompositeAudioClip(audio_layers)
             final_video = final_video.with_audio(final_audio)
             print(f"   ✅ Final audio composed and attached to video")
        else:
             print(f"   ⚠️  No audio layers to mix - video will be silent!")
        
        # I. Export to MP4
        if progress_callback: progress_callback({"status": "rendering", "progress": 20, "message": "Starting Encoding..."})
        timestamp = int(time.time())
        output_filename = f"{project_data.get('name', 'video')}_final_{timestamp}.mp4"
        output_path = os.path.join(EXPORT_DIR, output_filename)
        
        print(f"💾 Saving to {output_path}...")
        
        # Create user logger
        # Note: MoviePy 'logger' argument expects either 'bar', None, or a proglog logger
        logger = RenderLogger(progress_callback) if progress_callback else 'bar'

        final_video.write_videofile(
            output_path, 
            fps=24, 
            preset="ultrafast",  # Use 'medium' for better quality, 'ultrafast' for testing
            codec="libx264",
            audio_codec="aac",
            threads=1,
            ffmpeg_params=['-pix_fmt', 'yuv420p'], # Good for compatibility
            logger=logger
        )
        
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
