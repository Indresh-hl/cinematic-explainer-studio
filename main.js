/* ==========================================================================
   ISY WHY (@isy019) - VIDEO 01 (ACT 1) GSAP TIMELINE ORCHESTRATION
   Duration: 80.04 seconds (Exact match to act1_voiceover.mp3)
   ========================================================================== */

window.__timelines = window.__timelines || {};

// Create paused master timeline
const tl = gsap.timeline({ paused: true });

// Register on global window.__timelines object
window.__timelines["main"] = tl;

/* ==========================================================================
   SCENE 01: 02:14 AM DIGITAL VOID (0.0s – 8.0s)
   ========================================================================== */
tl.fromTo(
  "#clock-housing",
  { scale: 0.85, opacity: 0, y: 30 },
  { scale: 1.0, opacity: 1, y: 0, duration: 1.2, ease: "expo.out" },
  0.2
);

// Colon pulse animation
tl.fromTo(
  "#clock-colon",
  { opacity: 0.2 },
  { opacity: 1, duration: 0.5, repeat: 10, yoyo: true, ease: "sine.inOut" },
  0.5
);

// Slow camera push-in
tl.fromTo(
  "#clock-housing",
  { scale: 1.0 },
  { scale: 1.12, duration: 6.5, ease: "none" },
  1.4
);

// Subtitle 1 reveal
tl.fromTo(
  "#sub-01",
  { opacity: 0, y: 20 },
  { opacity: 1, y: 0, duration: 0.8, ease: "power3.out" },
  0.6
);
tl.to("#sub-01", { opacity: 0, y: -15, duration: 0.6, ease: "power2.in" }, 6.8);

/* ==========================================================================
   SCENE 02: SILENT DARK BEDROOM (8.0s – 17.5s)
   ========================================================================== */
tl.fromTo(
  "#bedroom-stage",
  { opacity: 0 },
  { opacity: 1, duration: 1.0, ease: "sine.inOut" },
  8.0
);

tl.fromTo(
  "#bed-silhouette",
  { scale: 0.9, y: 40, opacity: 0 },
  { scale: 1.0, y: 0, opacity: 1, duration: 1.8, ease: "power3.out" },
  8.2
);

tl.fromTo(
  "#blinds-shadow",
  { opacity: 0 },
  { opacity: 1, duration: 2.0, ease: "sine.inOut" },
  8.4
);

tl.fromTo(
  "#gaze-beam",
  { scaleY: 0, opacity: 0, transformOrigin: "bottom center" },
  { scaleY: 1, opacity: 0.7, duration: 1.5, ease: "power2.out" },
  10.0
);

// Subtitle 2 reveal
tl.fromTo(
  "#sub-02",
  { opacity: 0, y: 20 },
  { opacity: 1, y: 0, duration: 0.8, ease: "power3.out" },
  8.5
);
tl.to("#sub-02", { opacity: 0, y: -15, duration: 0.6, ease: "power2.in" }, 16.5);

/* ==========================================================================
   SCENE 03 & 04: THE 35mm NOCTURNAL SLIDE PROJECTOR (17.5s – 40.0s)
   ========================================================================== */
// Violent spotlight beam slam on
tl.fromTo(
  "#light-cone",
  { opacity: 0, scale: 0.3 },
  { opacity: 1, scale: 1.0, duration: 0.3, ease: "expo.out" },
  17.5
);

tl.fromTo(
  "#slide-carousel",
  { opacity: 0, scale: 0.75, y: 50 },
  { opacity: 1, scale: 1.0, y: 0, duration: 0.6, ease: "back.out(1.4)" },
  17.7
);

// Subtitle 3 reveal
tl.fromTo(
  "#sub-03",
  { opacity: 0, y: 20 },
  { opacity: 1, y: 0, duration: 0.8, ease: "power3.out" },
  17.8
);
tl.to("#sub-03", { opacity: 0, y: -15, duration: 0.5, ease: "power2.in" }, 23.5);

// Slide 1 is active from 17.5 to 24.5
// Slide 2 Transition: Handshake Fistbump (At 24.5s)
tl.set("#slide-1", { display: "none" }, 24.5);
tl.set("#slide-2", { display: "flex", opacity: 0, scale: 0.92 }, 24.5);
tl.to("#slide-2", { opacity: 1, scale: 1.0, duration: 0.4, ease: "power3.out" }, 24.55);

// Subtitle 4 reveal
tl.fromTo(
  "#sub-04",
  { opacity: 0, y: 20 },
  { opacity: 1, y: 0, duration: 0.8, ease: "power3.out" },
  24.0
);

// Slide 3 Transition: Presentation Voice Crack (At 31.5s)
tl.set("#slide-2", { display: "none" }, 31.5);
tl.set("#slide-3", { display: "flex", opacity: 0, scale: 0.92 }, 31.5);
tl.to("#slide-3", { opacity: 1, scale: 1.0, duration: 0.4, ease: "power3.out" }, 31.55);

tl.to("#sub-04", { opacity: 0, y: -15, duration: 0.6, ease: "power2.in" }, 39.2);

/* ==========================================================================
   SCENE 05: THERMAL HEAT MAP SURGE (40.0s – 54.0s)
   ========================================================================== */
tl.fromTo(
  "#thermal-portrait",
  { opacity: 0, scale: 0.85 },
  { opacity: 1, scale: 1.0, duration: 0.8, ease: "expo.out" },
  40.0
);

// Thermal glow intensity surge
tl.fromTo(
  "#thermal-glow",
  { opacity: 0.1 },
  { opacity: 0.9, duration: 3.5, ease: "power2.inOut" },
  40.5
);

// Eye pupil dilation / panic
tl.fromTo(
  "#eye-pupil",
  { scale: 0.6 },
  { scale: 1.35, duration: 1.5, ease: "elastic.out(1, 0.4)" },
  41.0
);

// Vitals HUD entrance
tl.fromTo(
  "#vitals-hud",
  { opacity: 0, x: 40 },
  { opacity: 1, x: 0, duration: 0.8, ease: "power3.out" },
  41.2
);

// Subtitle 5 reveal
tl.fromTo(
  "#sub-05",
  { opacity: 0, y: 20 },
  { opacity: 1, y: 0, duration: 0.8, ease: "power3.out" },
  40.5
);
tl.to("#sub-05", { opacity: 0, y: -15, duration: 0.6, ease: "power2.in" }, 52.8);

/* ==========================================================================
   SCENE 06: KINETIC IMPACT ("WHY NOW?") (54.0s – 70.0s)
   ========================================================================== */
tl.fromTo(
  "#title-why-now",
  { scale: 2.2, opacity: 0, y: -60 },
  { scale: 1.0, opacity: 1, y: 0, duration: 0.5, ease: "expo.out" },
  54.0
);

tl.fromTo(
  "#kinetic-line",
  { scaleX: 0, opacity: 0 },
  { scaleX: 1, opacity: 1, duration: 0.6, ease: "power3.out" },
  54.5
);

tl.fromTo(
  "#kinetic-sub",
  { opacity: 0, y: 15 },
  { opacity: 1, y: 0, duration: 0.6, ease: "power2.out" },
  54.8
);

tl.fromTo(
  "#festival-card",
  { opacity: 0, y: 40, scale: 0.9 },
  { opacity: 1, y: 0, scale: 1.0, duration: 0.8, ease: "back.out(1.5)" },
  56.0
);

// Subtitle 6 reveal
tl.fromTo(
  "#sub-06",
  { opacity: 0, y: 20 },
  { opacity: 1, y: 0, duration: 0.8, ease: "power3.out" },
  54.5
);
tl.to("#sub-06", { opacity: 0, y: -15, duration: 0.6, ease: "power2.in" }, 68.5);

/* ==========================================================================
   SCENE 07: THE SURVIVAL SIMULATION (70.0s – 80.04s)
   ========================================================================== */
tl.fromTo(
  "#neuro-schematic",
  { opacity: 0, scale: 0.88 },
  { opacity: 1, scale: 1.0, duration: 1.0, ease: "expo.out" },
  70.0
);

// Cortex pulsing wireframe
tl.fromTo(
  ".cortex-path",
  { strokeDashoffset: 100 },
  { strokeDashoffset: 0, duration: 2.5, ease: "power2.out" },
  70.2
);

// Amygdala red alarm pulse
tl.fromTo(
  "#node-amygdala",
  { scale: 0.8, fill: "#E63946" },
  { scale: 1.4, fill: "#FF0033", duration: 0.8, repeat: 8, yoyo: true, transformOrigin: "center center", ease: "sine.inOut" },
  70.5
);

tl.fromTo(
  "#neuro-status",
  { opacity: 0, x: 30 },
  { opacity: 1, x: 0, duration: 0.8, ease: "power3.out" },
  71.0
);

// Subtitle 7 reveal
tl.fromTo(
  "#sub-07",
  { opacity: 0, y: 20 },
  { opacity: 1, y: 0, duration: 0.8, ease: "power3.out" },
  70.2
);
