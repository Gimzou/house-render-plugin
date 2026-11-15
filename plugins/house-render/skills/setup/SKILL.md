---
name: setup
description: One-time machine setup for house-render. Finds or installs-guides Blender, detects the GPU for Cycles, and writes ~/.config/house-render/machine.json. Use on first use, when renders fail to start, or when the user changes computer.
---

# Setup (once per computer)

Talk in plain language: the user may not be technical.

1. **Find Blender.** Check, in order: `$BLENDER`, `/Applications/Blender.app/Contents/MacOS/Blender` (macOS), `blender` on PATH, `C:\Program Files\Blender Foundation\Blender*\blender.exe` (Windows). Run `<blender> --version`.
   - Not found: tell the user to install **Blender 4.5 LTS** from blender.org (free; it runs on Windows, Linux, Apple Silicon and Intel Macs). The engine is tested on 4.5 only, so prefer it over 5.x. Never download it yourself. Wait for them, then retry.
2. **Probe the machine** (headless, ~10 s):
   ```
   <blender> -b --python-expr "import bpy,platform;p=bpy.context.preferences.addons['cycles'].preferences
   for t in ('OPTIX','CUDA','METAL','HIP','ONEAPI'):
       try:
           p.compute_device_type=t; p.refresh_devices(); print('DEV',t,[d.name for d in p.devices if d.type==t])
       except Exception as e: print('DEV',t,'-')
   print('OS',platform.platform())"
   ```
   Pick the first backend with a device, in the order OPTIX > CUDA > METAL > HIP > ONEAPI, else `CPU`.
3. **Benchmark** (optional, about 2 minutes): copy the example to a temp folder first, because the plugin folder is a read-only cache (`cp -R ${CLAUDE_PLUGIN_ROOT}/examples/box-house /tmp/box-house`). Then build and preview it (see the `preview` skill), and time one Cycles render of `living` at `--scale 0.5 --samples 128`. Record the seconds per view. The log line `CYCLES DEVICE` confirms the GPU is used.
4. **Write** `~/.config/house-render/machine.json`:
   ```json
   {"blender": "<path>", "blender_version": "4.5.x", "cycles_device": "METAL|OPTIX|CUDA|HIP|ONEAPI|CPU",
    "eevee_ok": true, "cycles_sec_per_view_720p_128spp": 95, "measured": "<date>"}
   ```
5. Tell the user in one or two lines what was found, e.g. "Blender 4.5 found, Cycles on GPU (Metal), previews take about 30 s each." If Cycles is on the CPU, warn them that photoreal stills take 20 to 60 min each and should run overnight.

Every other skill reads `blender` from this file. If it's missing, run this skill first.
