# Heat Awareness Video: AI Prompt Pack (silent, 30 seconds)

**Goal:** a calm, silent ad-style video that loops in the dashboard's "Heat safety awareness" card.
**Final file:** `frontend/media/awareness.mp4` (optional poster: `frontend/media/poster.jpg`)
**Specs:** 16:9, 1920x1080, 24 fps, **no audio**, MP4 (H.264), under 15 MB. The dashboard shows tips on top, so do **not** burn text into the video.

Most AI video tools make 5-10 s per clip, so generate **3 clips of about 10 s** and join them (CapCut / DaVinci / Canva).
Paste the **Style block** at the start of every clip prompt so all three clips look like one film.

---

## Style block (paste before each clip)
> Cinematic documentary look, photorealistic, Indian city of Moradabad (Uttar Pradesh), real-world street scenes, warm golden-hour sunlight with visible heat haze, soft film grain, shallow depth of field, smooth slow camera movement, natural colours with teal shadows and amber highlights, 16:9, no text, no logos, no subtitles, no watermark, no dialogue, no sound.

## Clip 1 (0-10 s): The problem
> Wide shot of a busy Moradabad market street at midday, shimmering heat haze rising from the road, a vendor wiping sweat and covering his head with a cotton cloth, children walking in the harsh sun, a thermometer-like glow on the horizon. Slow push-in. Mood: tense, hot, tired. Ends on a close-up of a hand shielding eyes from the sun.

## Clip 2 (10-20 s): The right actions
> Warm, hopeful tone. A young woman in light cotton clothes drinks water from a steel bottle under a neem tree. A family walks to shade holding an umbrella. A volunteer places a clay water pot (matka) outside a shop for passers-by. A shopkeeper helps an elderly man to a cool shaded seat. Smooth handheld tracking shots, soft lens flare, colours cool down slightly from amber to soft teal.

## Clip 3 (20-30 s): The solution
> Cinematic drone shot rising over Moradabad rooftops: some roofs painted white and reflective, green trees lining a street, a small new park. Gentle transition to a clean glowing city map made of soft light points, with zones pulsing from red to green, then a calm sunset sky. Hopeful, bright, ending on a slow pull-back so the last frame can blend into the first for a loop.

## Negative prompt (if the tool has one)
> text, captions, logos, watermark, distorted faces, extra fingers, deformed hands, blurry, low resolution, flicker, gore, hospital emergency scenes, panic, political symbols, brand names

---

## Tool tips
- **Veo / Sora / Runway / Kling / Luma / Pika:** one clip per prompt, choose 16:9 and the longest duration (8-10 s). Turn audio off.
- **Keep it consistent:** reuse the same Style block, and if the tool allows, use the last frame of clip 1 as the first frame of clip 2 (image-to-video).
- **Join and export:** put the 3 clips on one timeline, add 0.5 s cross-dissolves, export MP4 without audio. In CapCut: Export > Resolution 1080p > Bitrate Recommended.
- **Make it small:** `ffmpeg -i in.mp4 -an -vf scale=1920:-2 -c:v libx264 -crf 26 -preset slow -movflags +faststart awareness.mp4`
- **Loop:** end the last clip on a similar frame to the first, or add a 1 s cross-dissolve from the last frame back to the first.

## On-screen tips (already built into the dashboard, rotating every 6 s)
1. Drink water every 20 minutes, even if you do not feel thirsty.
2. Avoid going outside between 12 pm and 4 pm on hot days.
3. Wear light, loose cotton clothes and cover your head.
4. Check on elderly neighbours, children and pets.
5. Dizzy, confused or very hot skin? Move to shade and call 108.

Edit the `tips` list near the bottom of `frontend/app.js` to change or translate them (for example into Hindi).

## Poster image prompt (optional, for `poster.jpg`)
> Photorealistic wide shot of a Moradabad street at golden hour with heat haze and a person drinking water in the shade, cinematic, 16:9, no text.
