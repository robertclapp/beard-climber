"""sfx.py - tiny chiptune sound effects (numpy synth -> WAV) and MP4 muxing (ffmpeg).

Sounds: pickup (rising arpeggio), clink (hard hat absorbs a hit), pop (hat pops off),
hurt (hit without a hat), spit (mouth throws a hazard), spit_hat (mouth throws a hard hat).
"""
import os, shutil, subprocess, tempfile, wave
import numpy as np

RATE = 22050


def _t(sec):
    return np.arange(int(RATE * sec)) / RATE


def _square(freq, t):
    return np.sign(np.sin(2 * np.pi * np.cumsum(np.broadcast_to(freq, t.shape)) / RATE))


def _env(t, decay):
    return np.exp(-t / decay)


def synth(kind):
    if kind == "pickup":
        parts = [0.5 * _square(f, _t(0.055)) * _env(_t(0.055), 0.08) for f in (523, 659, 784, 1047)]
        return np.concatenate(parts)
    if kind == "clink":
        t = _t(0.14)
        return 0.45 * (0.6 * _square(1760, t) + 0.4 * _square(2637, t)) * _env(t, 0.035)
    if kind == "pop":
        t = _t(0.18)
        sweep = 900 * (200 / 900) ** (t / t[-1])
        noise = np.random.default_rng(1).uniform(-1, 1, t.size) * _env(t, 0.02)
        return 0.5 * _square(sweep, t) * _env(t, 0.08) + 0.35 * noise
    if kind == "hurt":
        t = _t(0.22)
        return 0.4 * _square(300 * (120 / 300) ** (t / t[-1]), t) * _env(t, 0.12)
    if kind == "spit":
        t = _t(0.09)
        noise = np.random.default_rng(2).uniform(-1, 1, t.size)
        return 0.18 * (0.5 * noise + _square(180, t)) * _env(t, 0.03)
    if kind == "spit_hat":
        t = _t(0.08)
        return np.concatenate([0.3 * _square(f, t) * _env(t, 0.04) for f in (2093, 2637, 3136)])
    raise KeyError(kind)


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
        w.writeframes((x * 32000).astype("<i2").tobytes())


def write_all(sfx_dir):
    os.makedirs(sfx_dir, exist_ok=True)
    for k in ("pickup", "clink", "pop", "hurt", "spit", "spit_hat"):
        write_wav(os.path.join(sfx_dir, f"{k}.wav"), synth(k))


def make_mp4(frames, events, frame_ms, out_path, sfx_dir, scale=2):
    """frames: list of PIL images (1x). events: [(frame, sfx_kind)]. Needs ffmpeg."""
    ff = shutil.which("ffmpeg")
    if not ff:
        print("ffmpeg not found - skipping", out_path)
        return False
    write_all(sfx_dir)
    n = len(frames)
    audio = np.zeros(int(RATE * n * frame_ms / 1000) + RATE)
    for f, kind in events:
        if 0 <= f < n:
            x = synth(kind)
            i = int(RATE * f * frame_ms / 1000)
            audio[i:i + x.size] += x[: audio.size - i]
    with tempfile.TemporaryDirectory() as tmp:
        for i, fr in enumerate(frames):
            fr.convert("RGB").resize((fr.width * scale, fr.height * scale), 0).save(os.path.join(tmp, f"{i:04d}.png"))
        write_wav(os.path.join(tmp, "a.wav"), audio[: int(RATE * n * frame_ms / 1000)])
        cmd = [ff, "-y", "-loglevel", "error", "-framerate", f"{1000 / frame_ms:.4f}", "-i", os.path.join(tmp, "%04d.png"),
               "-i", os.path.join(tmp, "a.wav"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
               "-c:a", "aac", "-b:a", "96k", "-shortest", out_path]
        subprocess.run(cmd, check=True)
    return True
