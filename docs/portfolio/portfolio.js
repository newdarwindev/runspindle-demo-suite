/* Progressive enhancement only. Evidence, links and native video work without JS. */
'use strict';
(async () => {
  let runs;
  try {
    const response = await fetch('data/runs.json');
    if (!response.ok) throw new Error('Evidence index unavailable');
    runs = await response.json();
  } catch (_) {
    // Keep the static page and all direct evidence links useful if fetch fails.
    return;
  }
  for (const run of runs) {
    const card = document.getElementById(run.case);
    if (!card) continue;
    const video = card.querySelector('video');
    const clips = card.querySelector('.clip-select');
    const speed = card.querySelector('.speed-select');
    const status = card.querySelector('.playback-status');
    const base = `media/${run.runId}/`;
    const applySpeed = () => { video.defaultPlaybackRate = video.playbackRate = Number(speed.value); };
    applySpeed();
    video.addEventListener('loadedmetadata', applySpeed);
    speed.addEventListener('change', applySpeed);
    video.addEventListener('play', () => {
      // Avoid multiple videos playing off-screen at once.
      document.querySelectorAll('video').forEach(other => { if (other !== video) other.pause(); });
      status.textContent = '';
    });
    video.addEventListener('error', () => { status.textContent = 'This browser could not play this WebM capture. Open an individual clip below, or use the MP4 release reel.'; });
    clips.addEventListener('change', () => {
      const media = run.media[Number(clips.value)];
      video.pause();
      video.querySelector('source').src = base + media.clip;
      video.querySelector('track').src = base + media.captions;
      video.poster = base + media.poster;
      video.load();
      applySpeed();
      status.textContent = `Capture ${Number(clips.value) + 1} selected. Press play or replay to inspect it.`;
    });
    card.querySelector('.replay').addEventListener('click', async () => {
      try {
        video.currentTime = 0;
        applySpeed();
        await video.play();
      } catch (_) {
        status.textContent = 'Playback did not start. Try the video’s native play button or open the clip directly below.';
      }
    });
    card.querySelector('.controls').hidden = false;
  }
})();
