// Future Human Daily - Podcast Engine & Web Application
document.addEventListener('DOMContentLoaded', () => {
    // --- Episode Database ---
    const episodes = [
        {
            id: 'ep-002',
            number: 'EPISODE 002',
            date: 'September 27, 2026',
            title: 'Targeted Dream Incubation & Neuro-Hacking',
            subtitle: 'Can AI guide or record what happens inside your sleeping mind? MIT neuroscience vs biological reality checks.',
            duration: '5:05',
            durationSeconds: 305,
            audioUrl: 'audio/ep-002.mp3',
            tags: ['Neuroscience', 'MIT Dormio', 'Sleep Science', 'Dream Hacking'],
            script: [
                { time: '0:00', label: '[Intro]', text: 'I am your host Alex Mercer with Dr. Elena Vance, and today is September 27th, and you\'re listening to Future Human Daily. Today we are talking about Targeted Dream Incubation.' },
                { time: '0:45', label: '[Noodle Fingers & Taco Dreams]', text: 'Have you ever tried typing a text in a dream where your fingers turn to floppy wet noodles? Or flying on a giant taco over geometry class?' },
                { time: '1:45', label: '[MIT Dormio Device]', text: 'MIT Media Lab created Dormio to detect hypnagogia and inject acoustic cues directly into REM sleep.' },
                { time: '3:00', label: '[Sleep Side-Hustle Debate]', text: 'Alex wants to learn Japanese while sleeping, but Elena brings the biological reality check on glymphatic brain washing!' },
                { time: '4:30', label: '[Neuro-Marketing & Dream Ads]', text: 'Major soda brands testing audio cues during sleep—why our dreams are the last sanctuary of cognitive liberty.' }
            ],
            notes: `
                <h4>Episode Summary:</h4>
                <p>In Episode 002, Alex Mercer and Dr. Elena Vance debate Targeted Dream Incubation (TDI) and MIT's Dormio project, exploring the boundary between artistic inspiration and corporate neuro-marketing.</p>
                <br>
                <h4>Key Takeaways:</h4>
                <ul>
                    <li><strong>Hypnagogia Hacking:</strong> Guiding dream topics during the micro-seconds between awake and sleep.</li>
                    <li><strong>Glymphatic Maintenance:</strong> Why the brain needs unscripted sleep to flush toxic metabolic proteins.</li>
                    <li><strong>Cognitive Autonomy:</strong> Guarding our subconscious from commercial dream-ad injections.</li>
                </ul>
            `
        },
        {
            id: 'ep-001',
            number: 'EPISODE 001',
            date: 'September 26, 2026',
            title: 'The Age of Synthetic Telepathy',
            subtitle: 'Alex Mercer & Dr. Elena Vance simplify Brain-Computer Interfaces, neural bandwidth, and mind-to-mind intimacy.',
            duration: '5:48',
            durationSeconds: 348,
            audioUrl: 'audio/ep-001.mp3',
            tags: ['BCI', 'Neuralink', 'Cybernetics', 'Communication'],
            script: [
                { time: '0:00', label: '[Intro]', text: 'I am your host, Alex Mercer, with Dr. Elena Vance, and today is September 26th, and you\'re listening to Future Human Daily. Today we are talking about Synthetic Telepathy.' },
                { time: '0:45', label: '[Morning Coffee Analogy]', text: 'Have you ever tried explaining a crazy, vivid dream to your partner over morning coffee? You wave your hands around... and all that comes out is: "There was a dog, and I think it was blue?"' },
                { time: '1:30', label: '[The Stuck Song]', text: 'Or when a song is completely stuck in your head and you try humming it to your friend, and they look at you like you\'ve lost your mind!' },
                { time: '2:15', label: '[Bandwidth Bottleneck]', text: 'That frustration is the fundamental bottleneck of being human. Billions of thoughts firing... squeezed down through 40 words a minute.' },
                { time: '3:15', label: '[Clumsy Tech & Typos]', text: 'We stare at glowing glass rectangles all day, tapping thumbs like cavemen with tiny stones, getting into fights over misplaced emojis or auto-correct typos!' },
                { time: '4:15', label: '[BCI Breakthroughs]', text: 'Neuralink, Synchron, and Paradromics decoded sub-vocal neural intent. Your brain doesn\'t even need to move your mouth; the neural pattern IS the signal.' },
                { time: '5:30', label: '[Empathy Without Translation]', text: 'Imagine sitting on the couch next to someone you love... no words, no screens. You let them feel the exact warmth of your heart in real time.' },
                { time: '6:30', label: '[Neural Privacy & Outro]', text: 'We will need cognitive security for our minds tomorrow. Thank you for spending September 26th with us on Future Human Daily. Stay curious about the future!' }
            ],
            notes: `
                <h4>Episode Summary:</h4>
                <p>In this inaugural episode, we explore how high-bandwidth Brain-Computer Interfaces (BCIs) are ushering in the era of Synthetic Telepathy.</p>
                <br>
                <h4>Key Takeaways:</h4>
                <ul>
                    <li><strong>The Bandwidth Bottleneck:</strong> Why spoken language captures only a fraction of mental complexity.</li>
                    <li><strong>Two-Way Neural Loops:</strong> Reading and writing to the cortex simultaneously.</li>
                    <li><strong>Cognitive Privacy:</strong> Who owns your neural logs in a connected world?</li>
                </ul>
            `
        },
        {
            id: 'ep-002',
            number: 'EPISODE 002',
            date: 'August 1, 2026',
            title: 'Cities That Think: Ambient Intelligence',
            subtitle: 'What happens when our physical urban environment gains context awareness and autonomous adaptation.',
            duration: '5:10',
            durationSeconds: 310,
            tags: ['Smart Cities', 'IoT', 'AI', 'Urban Design'],
            script: [
                { time: '0:00', label: '[Intro]', text: 'Step outside into the city of 2030. The streetlights don\'t just illuminate; they sense air density, micro-traffic flows, and acoustic signatures. Welcome to Ambient Intelligence.' },
                { time: '1:15', label: '[The Shift]', text: 'Instead of clicking apps on glass screens, the computing fabric melts into the physical walls around us.' },
                { time: '3:30', label: '[Outro]', text: 'Stay tuned for tomorrow\'s deep dive into bio-engineering.' }
            ],
            notes: `<h4>Episode Summary:</h4><p>Exploring how ambient sensors and edge AI turn physical architecture into responsive environments.</p>`
        },
        {
            id: 'ep-003',
            number: 'EPISODE 003',
            date: 'August 2, 2026',
            title: 'Rewriting the Code of Life: CRISPR 2.0',
            subtitle: 'Epigenetic editing, disease eradication, and the ethics of human bio-design.',
            duration: '4:45',
            durationSeconds: 285,
            tags: ['Genomics', 'Biotech', 'Ethics'],
            script: [
                { time: '0:00', label: '[Intro]', text: 'DNA is no longer a static blueprint—it is software waiting to be compiled.' }
            ],
            notes: `<h4>Episode Summary:</h4><p>From base editing to epigenetic switches, how precision genomics is curing hereditary diseases.</p>`
        },
        {
            id: 'ep-004',
            number: 'EPISODE 004',
            date: 'August 3, 2026',
            title: 'The End of Solitude in Space',
            subtitle: 'Living on Mars: The psychological and technological realities of off-world colonies.',
            duration: '5:30',
            durationSeconds: 330,
            tags: ['Space', 'Mars', 'Psychology'],
            script: [
                { time: '0:00', label: '[Intro]', text: 'What happens to human identity when Earth is no longer a physical destination, but a distant blue dot?' }
            ],
            notes: `<h4>Episode Summary:</h4><p>Examining closed-loop ecosystems and community dynamics on the first Martian outposts.</p>`
        },
        {
            id: 'ep-005',
            number: 'EPISODE 005',
            date: 'August 4, 2026',
            title: 'Digital Afterlives & Memory Vaults',
            subtitle: 'Can interactive AI personas preserve our consciousness for future generations?',
            duration: '4:15',
            durationSeconds: 255,
            tags: ['AI', 'Philosophy', 'Digital Legacy'],
            script: [
                { time: '0:00', label: '[Intro]', text: 'Imagine having a conversation with your great-grandmother\'s digital shadow.' }
            ],
            notes: `<h4>Episode Summary:</h4><p>The ethics and technology behind generative memory avatars and digital legacy vaults.</p>`
        },
        {
            id: 'ep-006',
            number: 'EPISODE 006',
            date: 'August 5, 2026',
            title: 'The Post-Work Economy',
            subtitle: 'How artificial general intelligence and automation redefine human achievement.',
            duration: '5:00',
            durationSeconds: 300,
            tags: ['Economics', 'Automation', 'Future of Work'],
            script: [
                { time: '0:00', label: '[Intro]', text: 'When machines produce all material abundance, what becomes the true currency of human purpose?' }
            ],
            notes: `<h4>Episode Summary:</h4><p>Navigating universal basic assets and the shift toward creative human fulfillment.</p>`
        }
    ];

    // --- State Variables ---
    let currentEpIndex = 0;
    let isPlaying = false;
    let currentTime = 0;
    let playbackSpeed = 1.0;
    let activePitch = 1.1; // Default enthusiastic pitch
    let timerInterval = null;
    let synth = window.speechSynthesis;
    let currentUtterance = null;
    let availableVoices = [];
    let customAudio = null;
    let isCustomAudioPlaying = false;

    // --- DOM Elements ---
    const epNumberEl = document.getElementById('ep-number');
    const epDateEl = document.getElementById('ep-date');
    const epTitleEl = document.getElementById('ep-title');
    const epSubtitleEl = document.getElementById('ep-subtitle');
    const currentTimeEl = document.getElementById('current-time');
    const totalTimeEl = document.getElementById('total-time');
    const progressBar = document.getElementById('progress-bar');
    const progressContainer = document.getElementById('progress-container');
    const playBtn = document.getElementById('btn-play');
    const speedBtn = document.getElementById('btn-speed');
    const rewindBtn = document.getElementById('btn-rewind');
    const forwardBtn = document.getElementById('btn-forward');
    const likeBtn = document.getElementById('btn-like');
    const transcriptContainer = document.getElementById('transcript-container');
    const notesContainer = document.getElementById('notes-container');
    const episodesGrid = document.getElementById('episodes-grid');
    const searchInput = document.getElementById('episode-search');
    
    const voiceSelect = document.getElementById('voice-select');
    const pitchSlider = document.getElementById('pitch-slider');
    const pitchVal = document.getElementById('pitch-val');
    const audioFileInput = document.getElementById('audio-file-input');

    // --- Populate Browser Voices ---
    function loadVoices() {
        if (!synth) return;
        availableVoices = synth.getVoices().filter(v => v.lang.startsWith('en'));
        
        if (availableVoices.length === 0) {
            availableVoices = synth.getVoices();
        }

        voiceSelect.innerHTML = '';
        availableVoices.forEach((voice, i) => {
            const opt = document.createElement('option');
            opt.value = i;
            // Highlight natural / high-quality neural voices
            const isNatural = voice.name.includes('Natural') || voice.name.includes('Google') || voice.name.includes('Neural') || voice.name.includes('Premium');
            opt.textContent = `${voice.name} (${voice.lang})${isNatural ? ' ✨' : ''}`;
            if (isNatural) opt.selected = true;
            voiceSelect.appendChild(opt);
        });
    }

    loadVoices();
    if (synth && synth.onvoiceschanged !== undefined) {
        synth.onvoiceschanged = loadVoices;
    }

    const btnRecordMic = document.getElementById('btn-record-mic');
    const recDot = document.getElementById('rec-dot');
    const recBtnText = document.getElementById('rec-btn-text');
    let mediaRecorder = null;
    let audioChunks = [];
    let isRecordingMic = false;

    if (btnRecordMic) {
        btnRecordMic.addEventListener('click', async () => {
            if (!isRecordingMic) {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    mediaRecorder = new MediaRecorder(stream);
                    audioChunks = [];

                    mediaRecorder.ondataavailable = (event) => {
                        if (event.data.size > 0) audioChunks.push(event.data);
                    };

                    mediaRecorder.onstop = () => {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/mp3' });
                        const audioUrl = URL.createObjectURL(audioBlob);
                        stopPlayback();
                        
                        if (nativeAudioPlayer) {
                            nativeAudioPlayer.src = audioUrl;
                            nativeAudioPlayer.load();
                        }
                        customAudio = new Audio(audioUrl);
                        customAudio.onloadedmetadata = () => {
                            const durationMins = Math.floor(customAudio.duration / 60);
                            const durationSecs = Math.floor(customAudio.duration % 60);
                            totalTimeEl.textContent = `${durationMins}:${durationSecs < 10 ? '0' : ''}${durationSecs}`;
                        };
                        customAudio.ontimeupdate = () => {
                            currentTime = Math.floor(customAudio.currentTime);
                            updateProgressUI();
                            syncScriptHighlight();
                        };

                        alert("Recording finished! Click PLAY to listen to your voice recording with full visualization.");
                    };

                    mediaRecorder.start();
                    isRecordingMic = true;
                    recBtnText.textContent = "Stop Recording";
                    recDot.style.color = "#ef4444";
                    recDot.classList.add("pulse-dot");
                } catch (err) {
                    alert("Microphone access denied or unavailable: " + err.message);
                }
            } else {
                if (mediaRecorder && mediaRecorder.state !== "inactive") {
                    mediaRecorder.stop();
                    mediaRecorder.stream.getTracks().forEach(track => track.stop());
                }
                isRecordingMic = false;
                recBtnText.textContent = "Record My Voice";
                recDot.style.color = "";
                recDot.classList.remove("pulse-dot");
            }
        });
    }

    // Custom MP3 Audio Upload Listener
    audioFileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            stopPlayback();
            const objectUrl = URL.createObjectURL(file);
            customAudio = new Audio(objectUrl);
            
            customAudio.onloadedmetadata = () => {
                const durationMins = Math.floor(customAudio.duration / 60);
                const durationSecs = Math.floor(customAudio.duration % 60);
                totalTimeEl.textContent = `${durationMins}:${durationSecs < 10 ? '0' : ''}${durationSecs}`;
            };

            customAudio.ontimeupdate = () => {
                currentTime = Math.floor(customAudio.currentTime);
                updateProgressUI();
                syncScriptHighlight();
            };

            customAudio.onended = () => {
                stopPlayback();
            };

            alert(`Loaded custom voiceover file: ${file.name}! Click Play to listen with full visualization.`);
        }
    });
     const nativeAudioPlayer = document.getElementById('html-audio-player');

    // Sync native audio events with custom UI
    if (nativeAudioPlayer) {
        nativeAudioPlayer.addEventListener('play', () => {
            isPlaying = true;
            playBtn.innerHTML = '<i class="fa-solid fa-pause"></i>';
            drawWaveform();
        });

        nativeAudioPlayer.addEventListener('pause', () => {
            isPlaying = false;
            playBtn.innerHTML = '<i class="fa-solid fa-play"></i>';
        });

        nativeAudioPlayer.addEventListener('timeupdate', () => {
            currentTime = Math.floor(nativeAudioPlayer.currentTime);
            updateProgressUI();
            syncScriptHighlight();
        });

        nativeAudioPlayer.addEventListener('ended', () => {
            stopPlayback();
        });
    }

    // --- Audio Playback Logic ---
    function togglePlay() {
        if (isPlaying) {
            pausePlayback();
        } else {
            startPlayback();
        }
    }

    function startPlayback() {
        isPlaying = true;
        playBtn.innerHTML = '<i class="fa-solid fa-pause"></i>';
        drawWaveform();

        const currentEp = episodes[currentEpIndex];

        // 1. Try native audio player first
        if (nativeAudioPlayer && nativeAudioPlayer.src) {
            nativeAudioPlayer.playbackRate = playbackSpeed;
            const playPromise = nativeAudioPlayer.play();
            if (playPromise !== undefined) {
                playPromise.catch(error => {
                    console.warn("Native audio play deferred/blocked:", error);
                });
            }
            return;
        }

        // 2. Custom MP3 File
        if (customAudio) {
            customAudio.playbackRate = playbackSpeed;
            customAudio.play().catch(e => console.warn(e));
            return;
        }

        // 3. Fallback to speech synth
        playSpeechSynthFallback(currentEp);
    }

    function playSpeechSynthFallback(currentEp) {
        if (synth && 'speechSynthesis' in window) {
            synth.cancel();
            const fullScriptText = currentEp.script.map(s => s.text).join(' ');
            currentUtterance = new SpeechSynthesisUtterance(fullScriptText);
            currentUtterance.rate = playbackSpeed * 1.05;
            currentUtterance.pitch = activePitch;

            const selectedVoiceIndex = voiceSelect.value;
            if (availableVoices[selectedVoiceIndex]) {
                currentUtterance.voice = availableVoices[selectedVoiceIndex];
            }

            currentUtterance.onend = () => {
                stopPlayback();
            };

            synth.speak(currentUtterance);
        }

        if (timerInterval) clearInterval(timerInterval);
        timerInterval = setInterval(() => {
            currentTime += 1;
            if (currentTime >= currentEp.durationSeconds) {
                stopPlayback();
            } else {
                updateProgressUI();
                syncScriptHighlight();
            }
        }, 1000 / playbackSpeed);
    }

    function pausePlayback() {
        isPlaying = false;
        playBtn.innerHTML = '<i class="fa-solid fa-play"></i>';
        if (timerInterval) clearInterval(timerInterval);
        if (synth) synth.pause();
        if (customAudio) customAudio.pause();
    }

    function stopPlayback() {
        isPlaying = false;
        playBtn.innerHTML = '<i class="fa-solid fa-play"></i>';
        if (timerInterval) clearInterval(timerInterval);
        if (synth) synth.cancel();
        if (customAudio) {
            customAudio.pause();
            customAudio.currentTime = 0;
        }
        currentTime = 0;
        updateProgressUI();
    }

    function updateProgressUI() {
        const ep = episodes[currentEpIndex];
        const progressPercent = (currentTime / ep.durationSeconds) * 100;
        progressBar.style.width = `${progressPercent}%`;

        // Format time string
        const mins = Math.floor(currentTime / 60);
        const secs = Math.floor(currentTime % 60);
        currentTimeEl.textContent = `${mins}:${secs < 10 ? '0' : ''}${secs}`;
    }

    // --- Render Episode Data ---
    function loadEpisode(index) {
        currentEpIndex = index;
        const ep = episodes[index];
        
        stopPlayback();

        epNumberEl.textContent = ep.number;
        epDateEl.textContent = ep.date;
        epTitleEl.textContent = ep.title;
        epSubtitleEl.textContent = ep.subtitle;
        totalTimeEl.textContent = ep.duration;
        currentTime = 0;
        updateProgressUI();

        // Setup HTML5 Audio if audioUrl exists
        if (ep.audioUrl) {
            if (nativeAudioPlayer) {
                nativeAudioPlayer.src = ep.audioUrl;
                nativeAudioPlayer.load();
            }
            customAudio = new Audio(ep.audioUrl);
            customAudio.onloadedmetadata = () => {
                const durationMins = Math.floor(customAudio.duration / 60);
                const durationSecs = Math.floor(customAudio.duration % 60);
                totalTimeEl.textContent = `${durationMins}:${durationSecs < 10 ? '0' : ''}${durationSecs}`;
            };
            customAudio.ontimeupdate = () => {
                currentTime = Math.floor(customAudio.currentTime);
                updateProgressUI();
                syncScriptHighlight();
            };
            customAudio.onended = () => {
                stopPlayback();
            };
        } else {
            customAudio = null;
            if (nativeAudioPlayer) nativeAudioPlayer.src = '';
        }

        // Render Transcript
        transcriptContainer.innerHTML = '';
        ep.script.forEach((seg, idx) => {
            const segDiv = document.createElement('div');
            segDiv.className = `script-segment ${idx === 0 ? 'active-segment' : ''}`;
            segDiv.dataset.index = idx;
            segDiv.innerHTML = `
                <span class="segment-time">${seg.time} — ${seg.label}</span>
                <p>${seg.text}</p>
            `;
            transcriptContainer.appendChild(segDiv);
        });

        // Render Notes
        notesContainer.innerHTML = ep.notes;
    }

    function syncScriptHighlight() {
        const ep = episodes[currentEpIndex];
        const totalSegs = ep.script.length;
        const timePerSeg = ep.durationSeconds / totalSegs;
        const currentSegIndex = Math.min(Math.floor(currentTime / timePerSeg), totalSegs - 1);

        const segments = transcriptContainer.querySelectorAll('.script-segment');
        segments.forEach((seg, i) => {
            if (i === currentSegIndex) {
                seg.classList.add('active-segment');
                seg.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            } else {
                seg.classList.remove('active-segment');
            }
        });
    }

    // --- Controls Listeners ---
    playBtn.addEventListener('click', togglePlay);

    speedBtn.addEventListener('click', () => {
        const speeds = [1.0, 1.25, 1.5, 2.0];
        const nextIdx = (speeds.indexOf(playbackSpeed) + 1) % speeds.length;
        playbackSpeed = speeds[nextIdx];
        speedBtn.textContent = `${playbackSpeed}x`;

        if (isPlaying) {
            pausePlayback();
            startPlayback();
        }
    });

    rewindBtn.addEventListener('click', () => {
        currentTime = Math.max(0, currentTime - 10);
        if (customAudio) customAudio.currentTime = currentTime;
        updateProgressUI();
        syncScriptHighlight();
    });

    forwardBtn.addEventListener('click', () => {
        const ep = episodes[currentEpIndex];
        currentTime = Math.min(ep.durationSeconds, currentTime + 10);
        if (customAudio) customAudio.currentTime = currentTime;
        updateProgressUI();
        syncScriptHighlight();
    });

    progressContainer.addEventListener('click', (e) => {
        const rect = progressContainer.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const ratio = clickX / rect.width;
        const ep = episodes[currentEpIndex];
        currentTime = Math.floor(ratio * ep.durationSeconds);
        if (customAudio) customAudio.currentTime = currentTime;
        updateProgressUI();
        syncScriptHighlight();
    });

    likeBtn.addEventListener('click', () => {
        const icon = likeBtn.querySelector('i');
        if (icon.classList.contains('fa-regular')) {
            icon.className = 'fa-solid fa-heart';
            likeBtn.style.color = '#e11d48';
        } else {
            icon.className = 'fa-regular fa-heart';
            likeBtn.style.color = '';
        }
    });

    // --- Tab Controls ---
    tabTranscriptBtn.addEventListener('click', () => {
        tabTranscriptBtn.classList.add('active');
        tabNotesBtn.classList.remove('active');
        tabTranscript.classList.remove('hidden');
        tabNotes.classList.add('hidden');
    });

    tabNotesBtn.addEventListener('click', () => {
        tabNotesBtn.classList.add('active');
        tabTranscriptBtn.classList.remove('active');
        tabNotes.classList.add('hidden');
        tabNotes.classList.remove('hidden');
    });

    // --- Search Input ---
    searchInput.addEventListener('input', (e) => {
        renderEpisodesGrid(e.target.value);
    });

    // --- RSS Feed XML Exporter ---
    function generateRssXml() {
        return `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" 
    xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" 
    xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>Future Human Daily</title>
    <link>https://futurehumandaily.com</link>
    <language>en-us</language>
    <itunes:author>Future Human Media</itunes:author>
    <itunes:summary>A daily narration podcast exploring the frontier of Brain-Computer Interfaces, AI, and human evolution.</itunes:summary>
    <itunes:category text="Technology"/>
    <itunes:image href="https://futurehumandaily.com/assets/cover.jpg"/>
    
    ${episodes.map(ep => `
    <item>
      <title>${ep.number}: ${ep.title}</title>
      <itunes:episode>${ep.id.split('-')[1]}</itunes:episode>
      <description>${ep.subtitle}</description>
      <pubDate>${ep.date} 06:00:00 EST</pubDate>
      <enclosure url="https://futurehumandaily.com/audio/${ep.id}.mp3" length="1245000" type="audio/mpeg"/>
      <itunes:duration>${ep.duration}</itunes:duration>
    </item>`).join('\n')}
  </channel>
</rss>`;
    }

    btnRss.addEventListener('click', () => {
        rssXmlContent.textContent = generateRssXml();
        modalRss.classList.remove('hidden');
    });

    btnCloseModal.addEventListener('click', () => {
        modalRss.classList.add('hidden');
    });

    btnCopyRss.addEventListener('click', () => {
        navigator.clipboard.writeText(generateRssXml()).then(() => {
            btnCopyRss.innerHTML = '<i class="fa-solid fa-check"></i> Copied to Clipboard!';
            setTimeout(() => {
                btnCopyRss.innerHTML = '<i class="fa-regular fa-copy"></i> Copy XML Feed';
            }, 2000);
        });
    });

    // Initialize App
    loadEpisode(0);
    renderEpisodesGrid();
});
