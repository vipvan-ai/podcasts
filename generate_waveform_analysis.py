import os
import json
import csv
import base64
import numpy as np
import soundfile as sf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# 1. Load Audio
audio_path = r'C:\Users\12482\Downloads\tension.mp3'
json_path = r'C:\Users\12482\Downloads\syllables_detailed.json'
csv_path = r'C:\Users\12482\Downloads\tension_syllables_timing.csv'
plot_path = r'C:\Users\12482\Downloads\tension_waveform_syllables.png'
html_path = r'C:\Users\12482\Downloads\tension_waveform_interactive.html'

data, sr = sf.read(audio_path)
if data.ndim > 1:
    mono = np.mean(data, axis=1)
else:
    mono = data

duration_sec = len(mono) / sr
duration_ms = duration_sec * 1000
time_ms = np.linspace(0, duration_ms, len(mono))

with open(json_path, 'r', encoding='utf-8') as f:
    syllables = json.load(f)

# 2. Write CSV
with open(csv_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Index', 'Word', 'Syllable', 'Phonetic (IPA)', 'Start (ms)', 'End (ms)', 'Duration (ms)'])
    for s in syllables:
        writer.writerow([
            s.get('index', ''),
            s.get('word', ''),
            s.get('syllable', ''),
            s.get('phonetic', ''),
            s.get('start_ms', 0),
            s.get('end_ms', 0),
            s.get('end_ms', 0) - s.get('start_ms', 0)
        ])

print("CSV written successfully.")

# 3. Generate High-Res Multi-Panel Waveform Plot
# Downsample for crisp plotting
downsample = max(1, len(mono) // 20000)
t_down = time_ms[::downsample]
y_down = mono[::downsample]

fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(20, 12), dpi=150)
fig.patch.set_facecolor('#0f172a')

# Palette
accent_color = '#38bdf8'
accent_sec = '#818cf8'
text_color = '#e2e8f0'
grid_color = '#334155'

# Panel 1: Overview
ax1.set_facecolor('#1e293b')
ax1.plot(t_down, y_down, color=accent_color, lw=0.6, alpha=0.85)
ax1.fill_between(t_down, y_down, -y_down, color=accent_color, alpha=0.15)
ax1.axvline(10000, color='#f43f5e', linestyle='--', lw=1.5, label='10s Split Boundary')
ax1.set_title('Full Audio Waveform (0 - 20,736 ms) Overview', color=text_color, fontsize=13, fontweight='bold', pad=10)
ax1.set_xlabel('Time (ms)', color=text_color, fontsize=10)
ax1.set_ylabel('Amplitude', color=text_color, fontsize=10)
ax1.tick_params(colors=text_color)
ax1.grid(True, color=grid_color, linestyle=':', alpha=0.6)
ax1.set_xlim(0, duration_ms)
ax1.legend(loc='upper right', facecolor='#0f172a', edgecolor=grid_color, labelcolor=text_color)

# Panel 2: Part 1 (0 to 10s) with syllable labels
ax2.set_facecolor('#1e293b')
mask1 = t_down <= 10000
ax2.plot(t_down[mask1], y_down[mask1], color='#34d399', lw=0.8, alpha=0.9)
ax2.fill_between(t_down[mask1], y_down[mask1], -y_down[mask1], color='#34d399', alpha=0.15)
ax2.set_title('Part 1: 0 to 10,000 ms — Syllable Boundaries & Offsets', color=text_color, fontsize=13, fontweight='bold', pad=10)
ax2.set_xlabel('Time (ms)', color=text_color, fontsize=10)
ax2.set_ylabel('Amplitude', color=text_color, fontsize=10)
ax2.tick_params(colors=text_color)
ax2.grid(True, color=grid_color, linestyle=':', alpha=0.6)
ax2.set_xlim(0, 10000)

for i, s in enumerate(syllables):
    st = s['start_ms']
    en = s['end_ms']
    if st < 10000:
        ax2.axvline(st, color='#64748b', linestyle=':', lw=0.8, alpha=0.7)
        mid = (st + min(en, 10000)) / 2
        y_pos = 0.55 if i % 2 == 0 else -0.75
        label_text = f"{s['syllable']}\n({st}ms)"
        ax2.text(mid, y_pos, label_text, color='#f1f5f9', fontsize=6.5, ha='center', va='center',
                 bbox=dict(boxstyle='round,pad=0.2', facecolor='#1e1b4b', edgecolor='#6366f1', alpha=0.8, lw=0.5))

# Panel 3: Part 2 (10s to end) with syllable labels
ax3.set_facecolor('#1e293b')
mask2 = t_down >= 10000
ax3.plot(t_down[mask2], y_down[mask2], color='#fb923c', lw=0.8, alpha=0.9)
ax3.fill_between(t_down[mask2], y_down[mask2], -y_down[mask2], color='#fb923c', alpha=0.15)
ax3.set_title('Part 2: 10,000 ms to End — Syllable Boundaries & Offsets', color=text_color, fontsize=13, fontweight='bold', pad=10)
ax3.set_xlabel('Time (ms)', color=text_color, fontsize=10)
ax3.set_ylabel('Amplitude', color=text_color, fontsize=10)
ax3.tick_params(colors=text_color)
ax3.grid(True, color=grid_color, linestyle=':', alpha=0.6)
ax3.set_xlim(10000, duration_ms)

for i, s in enumerate(syllables):
    st = s['start_ms']
    en = s['end_ms']
    if en > 10000:
        ax3.axvline(st, color='#64748b', linestyle=':', lw=0.8, alpha=0.7)
        mid = (max(st, 10000) + en) / 2
        y_pos = 0.55 if i % 2 == 0 else -0.75
        label_text = f"{s['syllable']}\n({st}ms)"
        ax3.text(mid, y_pos, label_text, color='#f1f5f9', fontsize=6.5, ha='center', va='center',
                 bbox=dict(boxstyle='round,pad=0.2', facecolor='#31103f', edgecolor='#ec4899', alpha=0.8, lw=0.5))

plt.tight_layout()
plt.savefig(plot_path, facecolor=fig.get_facecolor(), edgecolor='none', dpi=150)
plt.close()
print("Plot image saved successfully to:", plot_path)

# 4. Generate Interactive Standalone HTML Waveform Visualizer
# Encode audio to base64 so HTML is 100% self-contained
with open(audio_path, 'rb') as f:
    audio_b64 = base64.b64encode(f.read()).decode('utf-8')

# Calculate waveform peaks (1000 bins) for lightning fast interactive rendering
n_bins = 1200
bin_size = len(mono) // n_bins
peaks_min = []
peaks_max = []
for b in range(n_bins):
    chunk = mono[b*bin_size : (b+1)*bin_size]
    peaks_min.append(float(np.min(chunk)))
    peaks_max.append(float(np.max(chunk)))

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Waveform & Syllable Millisecond Alignment</title>
<style>
  :root {{
    --bg: #0b0f19;
    --card: #111827;
    --border: #1f2937;
    --accent: #38bdf8;
    --accent2: #818cf8;
    --text: #f3f4f6;
    --text-muted: #9ca3af;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    padding: 24px;
    display: flex;
    flex-direction: column;
    align-items: center;
  }}
  .container {{
    max-width: 1300px;
    width: 100%;
  }}
  header {{
    margin-bottom: 24px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    border-bottom: 1px solid var(--border);
    padding-bottom: 16px;
  }}
  h1 {{ font-size: 1.6rem; font-weight: 700; color: #fff; }}
  .subtitle {{ font-size: 0.9rem; color: var(--text-muted); margin-top: 4px; }}
  .stats {{
    display: flex;
    gap: 16px;
  }}
  .badge {{
    background: #1e293b;
    border: 1px solid #334155;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--accent);
  }}
  .player-box {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 24px;
    box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5);
  }}
  .canvas-wrapper {{
    position: relative;
    width: 100%;
    height: 180px;
    background: #030712;
    border-radius: 8px;
    overflow: hidden;
    cursor: crosshair;
  }}
  canvas {{
    width: 100%;
    height: 100%;
    display: block;
  }}
  .cursor-line {{
    position: absolute;
    top: 0;
    bottom: 0;
    width: 2px;
    background: #f43f5e;
    pointer-events: none;
    transform: translateX(-50%);
    box-shadow: 0 0 8px #f43f5e;
  }}
  .controls {{
    display: flex;
    align-items: center;
    gap: 16px;
    margin-top: 16px;
  }}
  button {{
    background: linear-gradient(135deg, #0284c7, #2563eb);
    color: #fff;
    border: none;
    padding: 8px 18px;
    border-radius: 6px;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.2s;
  }}
  button:hover {{ opacity: 0.9; }}
  .current-time {{
    font-family: monospace;
    font-size: 1.1rem;
    color: var(--accent);
    min-width: 140px;
  }}
  .search-bar {{
    padding: 8px 12px;
    background: #1f2937;
    border: 1px solid #374151;
    color: #fff;
    border-radius: 6px;
    font-size: 0.9rem;
    width: 250px;
    margin-left: auto;
  }}
  .table-container {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    max-height: 520px;
    overflow-y: auto;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.88rem;
    text-align: left;
  }}
  thead {{
    position: sticky;
    top: 0;
    background: #1e293b;
    z-index: 10;
  }}
  th, td {{
    padding: 10px 14px;
    border-bottom: 1px solid #1f2937;
  }}
  th {{
    color: #94a3b8;
    text-transform: uppercase;
    font-size: 0.75rem;
    letter-spacing: 0.05em;
  }}
  tr.active {{
    background: rgba(56, 189, 248, 0.15);
  }}
  tr:hover {{
    background: rgba(255, 255, 255, 0.04);
    cursor: pointer;
  }}
  .time-cell {{
    font-family: monospace;
    color: #38bdf8;
    font-weight: 600;
  }}
  .syl-cell {{
    font-weight: 700;
    color: #f8fafc;
  }}
  .ipa-cell {{
    font-family: monospace;
    color: #a78bfa;
  }}
</style>
</head>
<body>
<div class="container">
  <header>
    <div>
      <h1>Acoustic Waveform & Syllable Alignment</h1>
      <div class="subtitle">File: tension.mp3 &bull; Duration: {duration_ms:.0f} ms ({duration_sec:.2f}s) &bull; Sample Rate: {sr} Hz</div>
    </div>
    <div class="stats">
      <div class="badge">111 Syllables</div>
      <div class="badge">44.1 kHz Stereo</div>
      <div class="badge">10s Split Ready</div>
    </div>
  </header>

  <div class="player-box">
    <div class="canvas-wrapper" id="canvasWrapper">
      <canvas id="waveformCanvas"></canvas>
      <div class="cursor-line" id="cursorLine" style="left: 0%;"></div>
    </div>
    <div class="controls">
      <button id="playBtn">Play / Pause</button>
      <div class="current-time" id="timeDisplay">0.000 ms</div>
      <audio id="audioElem" src="data:audio/mp3;base64,{audio_b64}"></audio>
      <input type="text" class="search-bar" id="searchBar" placeholder="Search word or syllable...">
    </div>
  </div>

  <div class="table-container">
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Word</th>
          <th>Syllable</th>
          <th>Phonetic (IPA)</th>
          <th>Start (ms)</th>
          <th>End (ms)</th>
          <th>Duration (ms)</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody id="sylTableBody">
      </tbody>
    </table>
  </div>
</div>

<script>
  const syllables = {json.dumps(syllables)};
  const peaksMin = {json.dumps(peaks_min)};
  const peaksMax = {json.dumps(peaks_max)};
  const durationMs = {duration_ms};

  const canvas = document.getElementById('waveformCanvas');
  const ctx = canvas.getContext('2d');
  const audio = document.getElementById('audioElem');
  const playBtn = document.getElementById('playBtn');
  const cursorLine = document.getElementById('cursorLine');
  const timeDisplay = document.getElementById('timeDisplay');
  const canvasWrapper = document.getElementById('canvasWrapper');
  const tableBody = document.getElementById('sylTableBody');
  const searchBar = document.getElementById('searchBar');

  function resizeCanvas() {{
    canvas.width = canvasWrapper.clientWidth * window.devicePixelRatio;
    canvas.height = canvasWrapper.clientHeight * window.devicePixelRatio;
    drawWaveform();
  }}
  window.addEventListener('resize', resizeCanvas);

  function drawWaveform() {{
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    const midY = h / 2;
    const n = peaksMin.length;

    // Draw syllable highlight zones
    syllables.forEach((s, idx) => {{
      const xStart = (s.start_ms / durationMs) * w;
      const xEnd = (s.end_ms / durationMs) * w;
      ctx.fillStyle = idx % 2 === 0 ? 'rgba(56, 189, 248, 0.08)' : 'rgba(129, 140, 248, 0.08)';
      ctx.fillRect(xStart, 0, xEnd - xStart, h);

      ctx.strokeStyle = 'rgba(148, 163, 184, 0.2)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(xStart, 0);
      ctx.lineTo(xStart, h);
      ctx.stroke();
    }});

    // Draw 10s boundary
    const x10 = (10000 / durationMs) * w;
    ctx.strokeStyle = '#f43f5e';
    ctx.lineWidth = 2 * window.devicePixelRatio;
    ctx.beginPath();
    ctx.moveTo(x10, 0);
    ctx.lineTo(x10, h);
    ctx.stroke();

    // Draw waveform bars
    for (let i = 0; i < n; i++) {{
      const x = (i / n) * w;
      const barW = Math.max(1, w / n);
      const top = midY - peaksMax[i] * (midY * 0.95);
      const bottom = midY - peaksMin[i] * (midY * 0.95);

      const grad = ctx.createLinearGradient(0, top, 0, bottom);
      grad.addColorStop(0, '#38bdf8');
      grad.addColorStop(0.5, '#60a5fa');
      grad.addColorStop(1, '#818cf8');

      ctx.fillStyle = grad;
      ctx.fillRect(x, top, barW, Math.max(1, bottom - top));
    }}
  }}

  function populateTable(filtered) {{
    tableBody.innerHTML = '';
    filtered.forEach((s) => {{
      const tr = document.createElement('tr');
      tr.id = `row-${{s.index}}`;
      const dur = s.end_ms - s.start_ms;
      tr.innerHTML = `
        <td>${{s.index}}</td>
        <td><strong>${{s.word}}</strong></td>
        <td class="syl-cell">${{s.syllable}}</td>
        <td class="ipa-cell">${{s.phonetic || '-'}}</td>
        <td class="time-cell">${{s.start_ms}} ms</td>
        <td class="time-cell">${{s.end_ms}} ms</td>
        <td class="time-cell">${{dur}} ms</td>
        <td><button style="padding:4px 8px;font-size:0.75rem;" onclick="playSyllable(${{s.start_ms}}, ${{s.end_ms}}, event)">Play</button></td>
      `;
      tr.addEventListener('click', () => {{
        seekToMs(s.start_ms);
      }});
      tableBody.appendChild(tr);
    }});
  }}

  window.playSyllable = function(startMs, endMs, e) {{
    e.stopPropagation();
    audio.currentTime = startMs / 1000;
    audio.play();
    const stopTime = endMs / 1000;
    const checkStop = () => {{
      if (audio.currentTime >= stopTime) {{
        audio.pause();
        audio.removeEventListener('timeupdate', checkStop);
      }}
    }};
    audio.addEventListener('timeupdate', checkStop);
  }};

  function seekToMs(ms) {{
    audio.currentTime = ms / 1000;
    updateCursor();
  }}

  function updateCursor() {{
    const currentMs = audio.currentTime * 1000;
    const pct = Math.min(100, Math.max(0, (currentMs / durationMs) * 100));
    cursorLine.style.left = `${{pct}}%`;
    timeDisplay.textContent = `${{currentMs.toFixed(0)}} ms / ${{durationMs.toFixed(0)}} ms`;

    // Highlight current row
    const curSyl = syllables.find(s => currentMs >= s.start_ms && currentMs <= s.end_ms);
    document.querySelectorAll('tr.active').forEach(r => r.classList.remove('active'));
    if (curSyl) {{
      const row = document.getElementById(`row-${{curSyl.index}}`);
      if (row) {{
        row.classList.add('active');
        row.scrollIntoView({{ block: 'nearest', behavior: 'smooth' }});
      }}
    }}
  }}

  playBtn.addEventListener('click', () => {{
    if (audio.paused) {{
      audio.play();
      playBtn.textContent = 'Pause';
    }} else {{
      audio.pause();
      playBtn.textContent = 'Play';
    }}
  }});

  audio.addEventListener('timeupdate', updateCursor);
  audio.addEventListener('ended', () => {{ playBtn.textContent = 'Play'; }});

  canvasWrapper.addEventListener('click', (e) => {{
    const rect = canvasWrapper.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const pct = clickX / rect.width;
    seekToMs(pct * durationMs);
  }});

  searchBar.addEventListener('input', (e) => {{
    const q = e.target.value.toLowerCase().trim();
    if (!q) {{
      populateTable(syllables);
      return;
    }}
    const filtered = syllables.filter(s =>
      s.word.toLowerCase().includes(q) ||
      s.syllable.toLowerCase().includes(q) ||
      (s.phonetic && s.phonetic.toLowerCase().includes(q))
    );
    populateTable(filtered);
  }});

  resizeCanvas();
  populateTable(syllables);
</script>
</body>
</html>
"""

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print("Interactive HTML visualizer saved to:", html_path)
