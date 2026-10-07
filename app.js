// Future Human Daily - Podcast Engine & Web Application
document.addEventListener('DOMContentLoaded', () => {
    // --- Episode Database ---
    const episodes = [
        {
            id: 'ep-010',
            number: 'EPISODE 010',
            date: 'October 6, 2026',
            title: 'Neural Dust & Ultrasound-Powered Micro BCI Transceivers',
            subtitle: 'Wireless ultrasound neural sensors smaller than sand grains! Alex Mercer & Dr. Elena Vance break down battery-free BCI motes, zero glial scar formation, and electro-ceutical therapies.',
            duration: '04:33',
            durationSeconds: 273,
            audioUrl: 'audio/ep-010.mp3',
            tags: ['Neural Dust', 'BCI', 'Ultrasound', 'Bio-Electronics'],
            script: [
                { time: '0:00', label: '[Intro]', text: 'I am your host Alex Mercer with Dr. Elena Vance, and today is October 6th, and you\'re listening to Future Human Daily. Today we are talking about Neural Dust.' },
                { time: '1:00', label: '[Rubber Ball Metaphor]', text: 'Acoustic ultrasound bouncing vs tissue attenuation.' },
                { time: '2:30', label: '[No Glial Scarring]', text: 'Microscopic sensors invisible to immune rejection.' },
                { time: '4:15', label: '[Electro-Ceutical Therapy]', text: 'Targeted nerve stimulation replacing daily pills.' }
            ],
            notes: `
                <h4>Episode Summary:</h4>
                <p>Wireless ultrasound neural sensors smaller than sand grains! Alex Mercer & Dr. Elena Vance break down battery-free BCI motes, zero glial scar formation, and electro-ceutical therapies.</p>
            `
        },

        {
            id: 'unwritten-code-ep-002',
            number: 'THE UNWRITTEN CODE: EP 002',
            date: 'October 6, 2026',
            title: 'EP 002: Who Pays on Date Three? (And The Ghosting Slow-Fade)',
            subtitle: 'Maya Lin & Julian Cross unpack modern dating etiquette: who pays on date three, the subtle art of the polite wallet reach, and why the slow-fade text is emotional cowardice.',
            duration: '10:33',
            durationSeconds: 633,
            audioUrl: 'audio/unwritten_code_ep002_20261006.mp3',
            tags: ['The Unwritten Code', 'Maya & Julian', 'Modern Dating', 'Etiquette'],
            script: [
                { time: '0:00', label: '[Maya]', text: '[cheerful] Welcome back to The Unwritten Code, everyone! I am Maya Lin alongside Julian Cross, and today is Tuesday, October sixth.' },
                { time: '0:45', label: '[Julian]', text: '[warmly] Today\'s dilemma comes from Ryan in Chicago: on date three, who is actually responsible for picking up the bill?' },
                { time: '2:30', label: '[Maya]', text: '[playfully] The performative wallet reach—pulling out your card while praying the other person insists on paying!' },
                { time: '5:15', label: '[Julian]', text: '[chuckles] The slow-fade text message: psychological torture disguised as politeness.' },
                { time: '8:45', label: '[The Code]', text: 'Handing down The New Dating Code: normalize the date three split, banish the slow-fade, and keep voice notes under 90 seconds.' }
            ],
            notes: `
                <h4>The Unwritten Code — Episode 002</h4>
                <p><strong>Hosts:</strong> Maya Lin & Julian Cross</p>
                <p>Maya & Julian unpack modern dating etiquette: who pays on date three, the subtle art of the polite wallet reach, and why the slow-fade text message is emotional cowardice compared to honest closure.</p>
                <br>
                <h4>The New Dating Code:</h4>
                <ul>
                    <li><strong>Rule 1:</strong> The Date Three Split or Take-Turns Law.</li>
                    <li><strong>Rule 2:</strong> The Sincere Wallet Rule—if you pull out your card, be prepared to swipe.</li>
                    <li><strong>Rule 3:</strong> The 48-Hour Closure Mandate—banish the slow-fade forever.</li>
                    <li><strong>Rule 4:</strong> The Audio Memo Cap—keep early voice notes under 90 seconds.</li>
                </ul>
            `
        },

        {
            id: 'unwritten-code-ep-001',
            number: 'THE UNWRITTEN CODE: EP 001',
            date: 'October 5, 2026',
            title: 'EP 001: The Slack Thumbs-Up vs. The Reply-All Disaster',
            subtitle: 'Maya Lin & Julian Cross launch The Unwritten Code: workplace Slack anxiety, the cold thumbs-up emoji, the "No-Hello" typing bubble, and reply-all disasters.',
            duration: '10:44',
            durationSeconds: 644,
            audioUrl: 'audio/unwritten_code_ep001_20261005.mp3',
            tags: ['The Unwritten Code', 'Maya & Julian', 'Workplace Etiquette', 'Slack Culture'],
            script: [
                { time: '0:00', label: '[Maya]', text: '[cheerful] Welcome to the premiere of The Unwritten Code! I am Maya Lin alongside Julian Cross.' },
                { time: '1:00', label: '[Julian]', text: '[warmly] Deciphering micro-messages and modern workplace communication.' },
                { time: '3:00', label: '[Maya]', text: '[playfully] The existential terror of receiving a naked yellow thumbs-up emoji from your boss on Slack.' },
                { time: '5:30', label: '[Julian]', text: '[chuckles] The Reply-All disaster and company email meltdowns.' },
                { time: '8:45', label: '[The Code]', text: 'The New Workplace Code: upgrade your emoji, never send a standalone "Hey", and respect inbox sanity.' }
            ],
            notes: `
                <h4>The Unwritten Code — Episode 001</h4>
                <p><strong>Hosts:</strong> Maya Lin & Julian Cross</p>
                <p>Maya & Julian launch The Unwritten Code by unpacking modern workplace messaging anxiety: why does a thumbs-up emoji on Slack feel passive-aggressive, the agony of the 'No-Hello' typing bubble, and who is still hitting reply-all to company emails?</p>
            `
        },

        {
            id: 'ep-weekend-sun',
            number: 'WEEKEND RECAP',
            date: 'October 4, 2026',
            title: 'Sunday AI Catchup: Claude Opus 5.5 & Cyber Defense',
            subtitle: 'Veda & Rami host a relaxed 20-minute weekend recap featuring Claude Opus 5.5, autonomous AI cyber defense agents, and solid-state energy.',
            duration: '20:51',
            durationSeconds: 1251,
            audioUrl: 'audio/ep-weekend-sun-20261004.mp3',
            tags: ['Weekend Recap', 'Veda & Rami', 'Sunday AI Catchup', 'Claude Opus 5.5'],
            script: [
                { time: '0:00', label: '[Intro]', text: 'Happy Sunday! Today we are looking back at the biggest AI & cyber defense stories of the week...' },
                { time: '2:15', label: '[Claude Opus 5.5]', text: 'Deep dive into Opus 5.5 reasoning, context window stability, and cross-domain synthesis.' },
                { time: '8:30', label: '[Autonomous Cyber Defense]', text: 'Ethical AI security agents discovering micro-vulnerabilities in real-time.' },
                { time: '14:00', label: '[Solid State Energy]', text: 'Hybrid quantum battery modeling and 5-minute EV fast charging.' }
            ],
            notes: `
                <h4>Episode Summary:</h4>
                <p>Welcome to the Future Human Daily Sunday Weekend Recap hosted by Veda and Rami! In this 20-minute Sunday edition, Veda and Rami unpack Claude Opus 5.5, autonomous AI cyber defense agents, and ultra-fast solid state battery simulations.</p>
                <br>
                <h4>Key Highlights:</h4>
                <ul>
                    <li><strong>Claude Opus 5.5 Deep Dive:</strong> Hierarchical reasoning & 2M token context stability.</li>
                    <li><strong>Autonomous Cyber Defense:</strong> Real-time software patch synthesis and ethical AI auditing.</li>
                    <li><strong>Solid-State Battery Tech:</strong> Quantum simulation breakthrough for 5-minute EV charging.</li>
                </ul>
            `
        },
        {
            id: 'unwritten-code-trailer',
            number: 'OFFICIAL TRAILER',
            date: 'October 3, 2026',
            title: 'Welcome to The Unwritten Code! (Premieres Monday, Oct 5)',
            subtitle: 'Meet Maya Lin & Julian Cross as they introduce the survival guide to modern human behavior, etiquette, and everyday micro-dilemmas.',
            duration: '1:08',
            durationSeconds: 68,
            audioUrl: 'audio/unwritten_code_trailer.mp3',
            tags: ['Official Trailer', 'Maya & Julian', 'Premieres Oct 5', 'Society & Etiquette'],
            script: [
                { time: '0:00', label: '[Maya]', text: '[warmly] [playfully] Have you ever received a Venmo request from a friend for two dollars and forty-seven cents... and wondered if modern society is completely broken?' },
                { time: '0:10', label: '[Julian]', text: '[chuckles] Or sat trapped in a twelve-person group chat wishing there was an eject button that didn\'t start an entire family war?' },
                { time: '0:20', label: '[Maya]', text: '[laughs] Welcome to The Unwritten Code—the survival guide to modern human behavior, etiquette, and life\'s weirdest everyday dilemmas.' },
                { time: '0:30', label: '[Julian]', text: '[warmly] I am Julian Cross...' },
                { time: '0:35', label: '[Maya]', text: '...and I am Maya Lin. Every weekday morning, we unpack the unspoken rules nobody taught you in school—from office Slack anxiety and first-date politics, to who actually owns the middle seat armrests on an airplane.' },
                { time: '0:50', label: '[Julian]', text: '[chuckles] Plus, every Saturday on The Weekend Docket, we put your wildest real-life dilemmas on trial and hand down the definitive verdict.' },
                { time: '0:58', label: '[Maya]', text: '[excitedly] Our daily drops start this Monday, October 5th! Hit the follow button right now on Spotify and Apple Podcasts so you never miss an episode.' },
                { time: '1:06', label: '[Julian]', text: '[warmly] See you Monday morning. Don\'t break the code!' }
            ],
            notes: `
                <h4>The Unwritten Code: Official Launch Trailer</h4>
                <p><strong>Premiering:</strong> Monday, October 5th, 2026.</p>
                <p>Join co-hosts <strong>Maya Lin</strong> & <strong>Julian Cross</strong> every weekday morning for 6–8 minute deep dives into the hilarious, awkward, and unwritten rules of modern life—plus <strong>The Weekend Docket</strong> every Saturday resolving listener dilemmas!</p>
            `
        },
        {
            id: 'ep-weekend-sat',
            number: 'WEEKEND RECAP',
            date: 'October 3, 2026',
            title: 'Saturday Weekend Recap: Tech Deep Dives & Weekly Catchup',
            subtitle: 'Veda & Rami host a relaxed weekend recap featuring deep tech stories, unhurried pacing, and continuous studio room tone.',
            duration: '5:42',
            durationSeconds: 342,
            audioUrl: 'audio/ep-weekend-sat-20261003.mp3',
            tags: ['Weekend Recap', 'Veda & Rami', 'Tech Catchup', 'Deep Dives'],
            script: [
                { time: '0:00', label: '[Intro]', text: 'Alex and Elena are off taking a well-deserved break today—so I am Veda with Rami...' },
                { time: '1:15', label: '[Weekly Highlights]', text: 'Recapping neuromorphic bio-acoustics, ambient energy harvesting, and mRNA oncology.' },
                { time: '3:30', label: '[Deep Tech Discussion]', text: 'Unhurried story transitions and deep-dive technical insights.' }
            ],
            notes: `
                <h4>Episode Summary:</h4>
                <p>Welcome to the Future Human Daily Weekend Recap hosted by Veda and Rami! In this Saturday episode, Veda and Rami take a relaxed, unhurried stroll through the week's biggest tech breakthroughs.</p>
                <br>
                <h4>Key Highlights:</h4>
                <ul>
                    <li><strong>Relaxed Weekend Pacing:</strong> Co-hosted by Veda & Rami.</li>
                    <li><strong>Continuous Studio Room Tone:</strong> Invisible zero-burst transitions.</li>
                    <li><strong>Weekly Tech Catchup:</strong> Deep dive into bio-acoustics & ambient energy.</li>
                </ul>
            `
        },
        {
            id: 'ep-008',
            number: 'EPISODE 008',
            date: 'October 2, 2026',
            title: 'Neuromorphic Acoustic AI Sensors & Ultrasound Diagnostics',
            subtitle: "Using micro-acoustic MEMS chips to listen to your body's internal biological symphony continuously with Dr. Elena Vance & Alex Mercer.",
            duration: '6:29',
            durationSeconds: 389,
            audioUrl: 'audio/ep-008.mp3',
            tags: ['Acoustic AI', 'Bio-Sensors', 'Cardiovascular', 'Preventive Care'],
            script: [
                { time: '0:00', label: '[Intro]', text: "I am your host Alex Mercer with Dr. Elena Vance, and today is October 2nd, and you're listening to Future Human Daily. Today we are talking about Neuromorphic Acoustic Sensors." },
                { time: '0:45', label: '[Car Mechanic Metaphor]', text: 'Listening to internal engine purrs vs a 10-second annual stethoscope check.' },
                { time: '1:45', label: '[Arterial Micro-Turbulence]', text: 'Detecting swirling blood flow micro-ripples 4 years before physical symptoms.' },
                { time: '3:15', label: '[Spiking Neural Microchips]', text: 'Low-power acoustic pattern recognition running on micro-watts.' },
                { time: '4:45', label: '[Nocturnal Pediatric Asthma]', text: 'Monitoring sleeping children to catch lung sound friction before asthma attacks.' }
            ],
            notes: `
                <h4>Episode Summary:</h4>
                <p>In Episode 008, Alex Mercer and Dr. Elena Vance explore how MEMS ultrasonic sensors and brain-inspired spiking microchips listen to arterial turbulence, pediatric asthma airway constriction, and internal heart sound signatures 24/7.</p>
                <br>
                <h4>Key Takeaways:</h4>
                <ul>
                    <li><strong>Continuous Bio-Acoustics:</strong> Wearable MEMS patches monitoring arterial blood flow turbulence.</li>
                    <li><strong>Early Detection:</strong> Spotting cardiovascular narrowing 4 years before symptoms occur.</li>
                    <li><strong>Spiking Neural Chips:</strong> On-device AI processing consuming micro-watts.</li>
                    <li><strong>Pediatric Asthma Monitoring:</strong> Preventing nocturnal asthma attacks before wheezing begins.</li>
                </ul>
            `
        },
        {
            id: 'ep-007',
            number: 'EPISODE 007',
            date: 'October 1, 2026',
            title: 'Personalized mRNA Cancer Vaccines & Immune Training',
            subtitle: "Training your body's T-cells to hunt down tumor mutations with surgical precision with Dr. Elena Vance & Alex Mercer.",
            duration: '6:32',
            durationSeconds: 392,
            audioUrl: 'audio/ep-007.mp3',
            tags: ['mRNA Vaccines', 'Oncology', 'Immune Training', 'Biotech'],
            script: [
                { time: '0:00', label: '[Intro]', text: "I am your host Alex Mercer with Dr. Elena Vance, and today is October 1st, and you're listening to Future Human Daily. Today we are talking about Personalized mRNA Cancer Vaccines." },
                { time: '0:45', label: '[Therapeutic vs Preventative]', text: 'Why cancer vaccines act like wanted posters for white blood cells after a tumor develops.' },
                { time: '1:45', label: '[Cellular Camouflage]', text: 'How tumors disguise themselves behind normal self-proteins.' },
                { time: '3:00', label: '[Neoantigen Target Practice]', text: 'Custom mRNA sequences training killer T-cells to target unique mutant flags.' },
                { time: '4:45', label: '[18-Day Bioprinting Turnaround]', text: 'Bringing personalized oncology from biopsy to arm injection in regional hospitals.' }
            ],
            notes: `
                <h4>Episode Summary:</h4>
                <p>In Episode 007, Alex Mercer and Dr. Elena Vance explore how AI genomic sequencing identifies unique tumor neoantigen flags, teaching killer T-cells to attack cancer while leaving healthy tissue untouched.</p>
                <br>
                <h4>Key Takeaways:</h4>
                <ul>
                    <li><strong>Therapeutic Vaccines:</strong> Training T-cells to attack existing tumors.</li>
                    <li><strong>Cellular Camouflage:</strong> Unmasking cancer cells hiding behind normal self-proteins.</li>
                    <li><strong>Neoantigen Target Practice:</strong> Printing custom mRNA wanted posters for white blood cells.</li>
                    <li><strong>18-Day Turnaround:</strong> Accelerating personalized vaccine production from months to weeks.</li>
                </ul>
            `
        },
        {
            id: 'pilot-social',
            number: 'PILOT PREVIEW',
            date: 'September 30, 2026',
            title: 'The $2.40 Venmo Invoice & Friendship Etiquette',
            subtitle: 'Pilot Episode of "The Unwritten Code" featuring Maya & Julian unpacking petty micro-invoices and modern friend etiquette.',
            duration: '0:48',
            durationSeconds: 48,
            audioUrl: 'audio/sample_social_maya_julian.mp3',
            tags: ['Social Dilemmas', 'Maya & Julian', 'Venmo Etiquette', 'Friendship'],
            script: [
                { time: '0:00', label: '[Maya]', text: '[sighs] [playfully] Julian, I need your immediate ruling on something that happened yesterday, because I think modern society might be officially broken.' },
                { time: '0:10', label: '[Julian]', text: '[chuckles] Oh boy. Whenever you start an episode with that tone, somebody either committed a major social faux pas or ruined a group dinner. What happened?' },
                { time: '0:22', label: '[Maya]', text: '[laughs] Worse. I went on a coffee run with a friend. She bought a pastry, I grabbed an iced latte. Three hours later, my phone buzzes with a Venmo request for two dollars and forty-seven cents. With a little croissant emoji attached!' },
                { time: '0:35', label: '[Julian]', text: '[groans] [chuckles] Two dollars and forty-seven cents? See, this is why we have The Unwritten Code! Under five dollars, you do not invoice a friend—you just store it in the universal karma bank and let them buy the next round!' }
            ],
            notes: `
                <h4>Pilot Concept:</h4>
                <p><strong>The Unwritten Code:</strong> Co-hosted by Maya (empathetic, observational, witty) and Julian (practical, dry humor, opinionated).</p>
                <br>
                <h4>The Verdict:</h4>
                <p>The "Under $5 Rule": Never invoice a friend for under $5. Put it in the universal karma bank and let them cover the next coffee.</p>
            `
        },
        {
            id: 'ep-006',
            number: 'EPISODE 006',
            date: 'September 30, 2026',
            title: 'Ambient Energy Harvesting & Battery-Free Electronics',
            subtitle: 'Powering smartwatches, medical sensors, and gadgets forever without ever plugging them into a wall outlet with Dr. Elena Vance & Alex Mercer.',
            duration: '5:45',
            durationSeconds: 345,
            audioUrl: 'audio/ep-006.mp3',
            tags: ['Energy Harvesting', 'Piezoelectric', 'Battery-Free', 'Green Tech'],
            script: [
                { time: '0:00', label: '[Intro]', text: "I am your host Alex Mercer with Dr. Elena Vance, and today is September 30th, and you're listening to Future Human Daily. Today we are talking about Ambient Energy Harvesting." },
                { time: '0:45', label: '[Low-Battery Anxiety Hook]', text: 'The modern panic of dead smartwatch batteries and tangled charging cables.' },
                { time: '1:30', label: '[Micro-Watt Harvesting Analogies]', text: 'Self-winding mechanical watches scaled to micro-electronics.' },
                { time: '2:45', label: '[Piezoelectric & TENG Mechanics]', text: 'Piezoelectric shoe insoles, clothing friction, and ambient Wi-Fi wave capture.' },
                { time: '4:15', label: '[Battery-Free Medical Implants]', text: 'Pacemakers and health monitors running 30 years without surgical battery replacement.' }
            ],
            notes: `
                <h4>Episode Summary:</h4>
                <p>In Episode 006, Alex Mercer and Dr. Elena Vance explore piezoelectric shoe insoles, triboelectric clothing, ambient radio-frequency harvesting, and solid-state supercapacitors that never wear out.</p>
                <br>
                <h4>Key Takeaways:</h4>
                <ul>
                    <li><strong>Kinetic Piezoelectric Harvesting:</strong> Converting footstep pressure into electrical voltage.</li>
                    <li><strong>Triboelectric Nanogenerators (TENGs):</strong> Capturing friction static electricity from movement.</li>
                    <li><strong>Ambient RF Harvesting:</strong> Pulling power out of background Wi-Fi and 5G signals.</li>
                    <li><strong>Battery-Free Pacemakers:</strong> Medical devices operating 30 years without battery swap surgeries.</li>
                </ul>
            `
        },
        {
            id: 'ep-005',
            number: 'EPISODE 005',
            date: 'September 29, 2026',
            title: 'Neuromorphic Optical Chips & Photonic Brain Computing',
            subtitle: 'Replacing silicon electrons with laser micro-channels to process artificial intelligence at light speed with Dr. Elena Vance & Alex Mercer.',
            duration: '3:40',
            durationSeconds: 220,
            audioUrl: 'audio/ep-005.mp3',
            tags: ['Photonic Computing', 'Neuromorphic Chips', 'Laser AI', 'Zero-Heat Compute'],
            script: [
                { time: '0:00', label: '[Intro]', text: 'I am your host Alex Mercer with Dr. Elena Vance, and today is September 29th, and you\'re listening to Future Human Daily. Today we are talking about Neuromorphic Optical Chips.' },
                { time: '0:45', label: '[Silicon Thermal Bottleneck]', text: 'Why traditional GPUs are hitting physical heat and power walls during matrix operations.' },
                { time: '1:30', label: '[Photonic Integrated Circuits]', text: 'Replacing copper interconnects with laser micro-channels to compute at the speed of light.' },
                { time: '2:30', label: '[Phase-Change Optical Synapses]', text: 'Storing neural weights and computing memory directly inside glass channels.' },
                { time: '3:20', label: '[Zero-Heat Edge Intelligence]', text: 'Running frontier AI models on lightweight devices without cooling fans or massive power grids.' }
            ],
            notes: `
                <h4>Episode Summary:</h4>
                <p>In Episode 005, Alex Mercer and Dr. Elena Vance explore how laser interference, optical waveguides, and phase-change materials enable zero-latency neural network processing without heat dissipation walls.</p>
                <br>
                <h4>Key Takeaways:</h4>
                <ul>
                    <li><strong>Photonic Integrated Circuits:</strong> Replacing copper interconnects with micro-laser channels.</li>
                    <li><strong>Passive Optical Matrix Multiplication:</strong> Computing AI calculations instantaneously as light passes through glass.</li>
                    <li><strong>Phase-Change Optical Synapses:</strong> Storing weights and memory directly inside optical channels.</li>
                    <li><strong>Zero-Heat Edge Intelligence:</strong> Running frontier AI models on lightweight devices without cooling fans.</li>
                </ul>
            `
        },
        {
            id: 'ep-004',
            number: 'EPISODE 004',
            date: 'September 28, 2026',
            title: 'Quantum Biomagnetism & Non-Invasive Brain Mapping',
            subtitle: 'Optically pumped quantum sensors, room-temperature MEG helmets, and real-time AI noise cancellation with Dr. Elena Vance & Alex Mercer.',
            duration: '3:42',
            durationSeconds: 222,
            audioUrl: 'audio/ep-004.mp3',
            tags: ['Neuroscience', 'Quantum Sensors', 'Biomagnetism', 'AI Noise Cancellation'],
            script: [
                { time: '0:00', label: '[Intro]', text: 'I am your host Alex Mercer with Dr. Elena Vance, and today is September 28th, and you\'re listening to Future Human Daily. Today we are talking about Quantum Biomagnetism.' },
                { time: '0:45', label: '[Femtotesla Signal Challenge]', text: 'Measuring neural magnetic flux a billion times weaker than Earth\'s magnetic field.' },
                { time: '1:45', label: '[Optically Pumped Magnetometers]', text: 'Replacing liquid-helium cryogenic MEG rooms with laser-heated rubidium vapor microchips.' },
                { time: '2:45', label: '[AI Spatial Filtering]', text: 'Generative AI spatial models filtering out subway and elevator magnetic interference in real time.' }
            ],
            notes: `
                <h4>Episode Summary:</h4>
                <p>In Episode 004, Alex Mercer and Dr. Elena Vance explore Optically Pumped Magnetometers (OPMs), room-temperature MEG helmets, and non-invasive functional brain imaging.</p>
                <br>
                <h4>Key Takeaways:</h4>
                <ul>
                    <li><strong>Femtotesla Sensitivity:</strong> Reading neural magnetic activity down to single millisecond precision.</li>
                    <li><strong>Room-Temperature Microchips:</strong> Eliminating liquid helium cryogenics for wearable quantum helmets.</li>
                    <li><strong>AI Spatial Cancellation:</strong> Machine learning models isolating brain signals from urban ambient magnetic noise.</li>
                </ul>
            `
        },
        {
            id: 'ep-003',
            number: 'EPISODE 003',
            date: 'September 27, 2026',
            title: 'Cellular Reprogramming & Resetting Biological Age Clocks',
            subtitle: 'Yamanaka factors, partial epigenetic resets, and extending human healthspan with Dr. Elena Vance & Alex Mercer.',
            duration: '4:18',
            durationSeconds: 258,
            audioUrl: 'audio/ep-003.mp3',
            tags: ['Biotech', 'Longevity', 'Yamanaka Factors', 'Epigenetics'],
            script: [
                { time: '0:00', label: '[Intro]', text: 'I am your host Alex Mercer with Dr. Elena Vance, and today is September 27th, and you\'re listening to Future Human Daily. Today we are talking about Cellular Reprogramming.' },
                { time: '0:45', label: '[Software Reset Analogy]', text: 'Imagine if you could wipe the temporary cache on your body\'s cells, restoring them back to factory settings.' },
                { time: '1:30', label: '[Yamanaka Factors]', text: 'The four transcription factors (Oct4, Sox2, Klf4, c-Myc) discovered by Shinya Yamanaka in 2006.' },
                { time: '2:30', label: '[Partial Reprogramming]', text: 'Pulse-dosing cells to reset biological age markers without losing specialized identity.' },
                { time: '3:30', label: '[Compression of Morbidity]', text: 'Extending healthspan so human beings stay biologically 35 until their nineties.' }
            ],
            notes: `
                <h4>Episode Summary:</h4>
                <p>In Episode 003, Alex Mercer and Dr. Elena Vance explore Yamanaka Factors, partial epigenetic resets, and reversing biological cellular age in living tissue.</p>
                <br>
                <h4>Key Takeaways:</h4>
                <ul>
                    <li><strong>Yamanaka Factors:</strong> Molecular transcription factors that erase cellular epigenetic marks.</li>
                    <li><strong>Partial Resetting:</strong> Restoring youthfulness without triggering pluripotency or cancer.</li>
                    <li><strong>Compression of Morbidity:</strong> Maximizing healthspan over pure numerical lifespan.</li>
                </ul>
            `
        },
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
