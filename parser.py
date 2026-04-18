from PIL import Image, ImageSequence
import numpy as np
from pathlib import Path
import shutil
from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
root = r"terrainworld/Font"

Path(r"terrainworld/Font-white").mkdir(parents=True, exist_ok=True)

def scan(path):
    img = Image.open(root+path)
    tile = np.array(img)
    Path("Font-white"+path).mkdir(parents=True, exist_ok=True)
    for i0 in range(16):
        for j0 in range(16):
            if (tile[i0,j0] == np.array([0,0,0,255],np.uint8)).all():
                tile[i0,j0]=np.array([255,255,255,255],np.uint8)
    x = Image.fromarray(tile)
    x.save(root+"-white"+path)

def scangif(path):
    src_path = root+path
    img = Image.open(src_path)
    width, height = img.size  # (w, h)
    Path(root+"-white"+path).mkdir(parents=True, exist_ok=True)

    for y in range(0, height, 16):
        for x in range(0, width, 16):
            frames = []
            durations_sec = []
            prev_raw_tile = None
            prev_dur_ms = None
            n_src = getattr(img, "n_frames", 1)
            first_raw_tile = None
            for frame_idx in range(n_src):
                img.seek(frame_idx)
                frame_rgba = img.convert("RGBA")
                raw_tile = np.array(frame_rgba)[y:y+16, x:x+16]
                tile = raw_tile.copy()
                if frame_idx == 0:
                    first_raw_tile = raw_tile.copy()
                dur_ms = max(10, int(img.info.get("duration", 100)))
                # If current raw tile equals previous
                if (
                    prev_raw_tile is not None
                    and np.array_equal(raw_tile, prev_raw_tile)
                ):
                    # Prefer changing a visible pixel very slightly but enough to survive palette quantization
                    opaque_idxs = np.argwhere(raw_tile[:, :, 3] > 0)
                    # Flip MSB of blue channel (0x80) to ensure palette difference while keeping change localized to 1px
                    delta = 0x80 if (frame_idx % 2 == 1) else 0x40
                    if opaque_idxs.size > 0:
                        oy, ox = opaque_idxs[0]
                        b = int(raw_tile[oy, ox, 2])
                        tile[oy, ox, 2] = (b ^ delta) & 0xFF
                    else:
                        # If fully transparent tile, tweak a fixed pixel anyway
                        ty, tx = 0, 0
                        b = int(raw_tile[ty, tx, 2])
                        tile[ty, tx, 2] = (b ^ delta) & 0xFF

                # Ensure last frame differs from first (avoid loop-merge optimization)
                if (
                    n_src > 1 and frame_idx == n_src - 1 and first_raw_tile is not None
                    and np.array_equal(raw_tile, first_raw_tile)
                ):
                    opaque_idxs = np.argwhere(raw_tile[:, :, 3] > 0)
                    delta2 = 0x20  # smaller toggle so we don't over-modify
                    if opaque_idxs.size > 0:
                        oy, ox = opaque_idxs[0]
                        b = int(tile[oy, ox, 2])
                        tile[oy, ox, 2] = (b ^ delta2) & 0xFF
                    else:
                        ty, tx = 0, 0
                        b = int(tile[ty, tx, 2])
                        tile[ty, tx, 2] = (b ^ delta2) & 0xFF

                frames.append(tile[:, :, :3])  # RGB only (avoid mask path issues)
                durations_sec.append(dur_ms / 1000.0)
                prev_raw_tile = raw_tile
                prev_dur_ms = dur_ms

            out_path = (
                root+"-parsed"+path+"/tile"+str(int(y/16)*int(width/16)+int(x/16))
            )
            # Ensure output directory exists
            Path(out_path).parent.mkdir(parents=True, exist_ok=True)

            # Sanitize frames for MoviePy: uint8, 3 channels, contiguous
            frames_rgb = []
            for f in frames:
                fr = f
                if fr.ndim == 2:
                    fr = np.stack([fr, fr, fr], axis=2)
                elif fr.ndim == 3 and fr.shape[2] >= 3:
                    fr = fr[:, :, :3]
                else:
                    fr = np.zeros((fr.shape[0], fr.shape[1], 3), dtype=np.uint8)
                if fr.dtype != np.uint8:
                    fr = fr.astype(np.uint8)
                fr = np.ascontiguousarray(fr)
                frames_rgb.append(fr)

            # Write GIF using MoviePy (no 'program' kwarg in MoviePy 2.x)
            try:
                clip = ImageSequenceClip(frames_rgb, durations=durations_sec)
                clip.write_gif(out_path, loop=0, logger=None)
            except Exception as e:
                print("write_gif failed for", out_path, "=>", repr(e))
                try:
                    shapes = list({fr.shape for fr in frames_rgb})
                    print("debug:", "n_frames=", len(frames_rgb), "shapes=", shapes, "dtype0=", frames_rgb[0].dtype if frames_rgb else None)
                except Exception as _e:
                    print("debug failed:", repr(_e))

            # Verify and fallback to Pillow writer if frames collapsed
            try:
                if Path(out_path).exists():
                    with Image.open(out_path) as chk_im:
                        saved_n = getattr(chk_im, "n_frames", 1)
                    if saved_n < len(frames_rgb):
                        # Fallback: Pillow GIF writer (no optimization)
                        durations_ms = [max(10, int(round(s * 1000))) for s in durations_sec]
                        pil_frames = [Image.fromarray(fr) for fr in frames_rgb]
                        # Convert to paletted images; use adaptive palette to keep colors
                        pal_frames = [im.convert('P', palette=Image.ADAPTIVE, colors=256) for im in pil_frames]
                        pal_frames[0].save(
                            out_path,
                            save_all=True,
                            append_images=pal_frames[1:],
                            loop=0,
                            duration=durations_ms,
                            disposal=2,
                            optimize=False,
                        )
                        print("Fallback Pillow GIF writer used:", out_path)
            except Exception as e:
                print("fallback verification/save failed for", out_path, "=>", repr(e))
def scandir(path):
    print(path)
    # Check and delete existing parsed directory if it exists
    parsed_dir = Path(root+"-white"+path)
    if parsed_dir.exists():
        shutil.rmtree(parsed_dir)
    parsed_dir.mkdir(parents=True, exist_ok=True)
    
    target = Path(root+path)
    print(target)
    print([i.name for i in target.iterdir()])
    for item in target.iterdir():
        if (item.is_dir() or item.suffix in [".png",".gif"]) and not item.name.startswith("."):
            if item.suffix == ".png":
                scan(path+"/"+item.name)
            elif item.suffix == ".gif":
                scangif(path+"/"+item.name)
            else:
                scandir(path+"/"+item.name)
scandir("")