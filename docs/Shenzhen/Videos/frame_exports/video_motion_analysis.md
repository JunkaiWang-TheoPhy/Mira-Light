# Shenzhen Videos Motion Analysis

## Method

- Source directory: `docs/Shenzhen/Videos/`
- Videos analyzed: `01` through `08`
- Extraction method: `ffmpeg` uniform sampling
- Sampling density: `20` evenly spaced frames per video
- Output layout:
  - Per-video frame directory: `frame_exports/<video_name>/`
  - Per-video contact sheet: `frame_exports/<video_name>_contact.jpg`
- Each extracted frame has an overlaid timestamp for stage-by-stage review.

## Assets

1. `01_20260425_043820_01_contact.jpg`
2. `02_20260425_043823_01_contact.jpg`
3. `03_20260425_043824_01_contact.jpg`
4. `04_20260425_043825_01_contact.jpg`
5. `05_20260425_043828_01_contact.jpg`
6. `06_20260425_043829_01_contact.jpg`
7. `07_20260425_043829_02_contact.jpg`
8. `08_20260425_043832_01_contact.jpg`

Per-video interpretation docs:

1. `01_20260425_043820_01-解读.md`
2. `02_20260425_043823_01-解读.md`
3. `03_20260425_043824_01-解读.md`
4. `04_20260425_043825_01-解读.md`
5. `05_20260425_043828_01-解读.md`
6. `06_20260425_043829_01-解读.md`
7. `07_20260425_043829_02-解读.md`
8. `08_20260425_043832_01-解读.md`

## Video 01

- File: `01_20260425_043820_01.mp4`
- Duration: `76.6s`
- Contact sheet: `frame_exports/01_20260425_043820_01_contact.jpg`

Observed full motion process:

1. Starts in a relatively low, left-leaning pose close to the tabletop.
2. Slowly unfolds upward toward a more centered and attentive posture.
3. Holds a calmer middle pose for a while instead of jumping directly into large motion.
4. Re-enters a deeper side lean and forward/down dip in the later half.
5. Ends in a low-attention tabletop-oriented pose rather than a fully collapsed rest.

Motion reading:

- This clip reads as a slow wake/open/settle pattern with a later exploratory dip.
- The movement is broad-phase and deliberate, not a tight repetitive micro-motion.

## Video 02

- File: `02_20260425_043823_01.mp4`
- Duration: `133.7s`
- Contact sheet: `frame_exports/02_20260425_043823_01_contact.jpg`

Observed full motion process:

1. Early segment includes guest/operator repositioning around the robot while the robot stays near a neutral waiting state.
2. The robot gradually orients toward the guest and incoming hand.
3. It performs one or more tentative lean-ins, as if inspecting or approaching cautiously.
4. Mid-to-late segment includes a shy partial retreat rather than a single direct commit.
5. It then re-approaches and finishes in a centered, attentive acknowledgement pose.

Motion reading:

- This is the clearest "cautious introduction" pattern in the set.
- The rhythm is: notice -> approach -> hesitate -> re-approach -> settle.

## Video 03

- File: `03_20260425_043824_01.mp4`
- Duration: `55.3s`
- Contact sheet: `frame_exports/03_20260425_043824_01_contact.jpg`

Observed full motion process:

1. Starts already facing the guest hand.
2. Moves closer and lowers itself into the hand zone.
3. Slides under or along the palm area and stays in close contact.
4. Performs sustained short-range nuzzling with compact vertical and horizontal oscillation.
5. Extends farther outward when the hand moves, producing a short follow behavior.
6. Ends in an affectionate, extended near-hand pose.

Motion reading:

- This is a strong reference for "hand nuzzle / touch affection".
- The key is not large travel distance, but maintaining intimate distance while doing small rub-like motions.

## Video 04

- File: `04_20260425_043825_01.mp4`
- Duration: `21.2s`
- Contact sheet: `frame_exports/04_20260425_043825_01_contact.jpg`

Observed full motion process:

1. Starts already oriented toward a tabletop-side target.
2. Maintains attention with very small corrections for most of the clip.
3. In the final third, the robot makes one clearer forward/down reach.
4. Ends extended toward the moved target instead of snapping back to center.

Motion reading:

- This clip is short and reads like a compact tabletop follow / target follow demo.
- The important characteristic is the late decisive reach after a period of smaller tracking corrections.

## Video 05

- File: `05_20260425_043828_01.mp4`
- Duration: `47.8s`
- Contact sheet: `frame_exports/05_20260425_043828_01_contact.jpg`

Observed full motion process:

1. Starts in an elevated, engaged pose toward the guest.
2. Stays in the upper-left working envelope with repeated compact posture shifts rather than long reaches.
3. Mid clip keeps a visibly animated, expressive pose while the guest reacts.
4. Late clip softens into a lower dip and then returns toward a more centered stance.
5. Ends calmer than the middle section instead of stopping abruptly.

Motion reading:

- Compared with the tracking clips, this one reads more like expressive/emotional motion than precise target pursuit.
- The visible movement is compact and rhythmic; the framing is also more guest-dominant than robot-dominant.
- If this clip is used as choreography ground truth, a denser frame pass or direct playback review would still help before final scripting.

## Video 06

- File: `06_20260425_043829_01.mp4`
- Duration: `17.0s`
- Contact sheet: `frame_exports/06_20260425_043829_01_contact.jpg`

Observed full motion process:

1. Starts already turned toward one side, as if attention has shifted to a departing guest.
2. Makes a smooth small pivot/raise toward the guest side.
3. Middle segment shows a compact acknowledgement gesture, likely a nod-like goodbye beat.
4. The pose then softens and lowers slightly.
5. Ends in a gentler, quieter farewell posture.

Motion reading:

- This is a concise farewell beat, not a long multi-stage scene.
- The strongest pattern is: look over -> acknowledge -> soften -> hold.

## Video 07

- File: `07_20260425_043829_02.mp4`
- Duration: `51.8s`
- Contact sheet: `frame_exports/07_20260425_043829_02_contact.jpg`

Observed full motion process:

1. Starts from an upright attentive pose.
2. Passes through a centered mid pose rather than dropping immediately.
3. Gradually extends outward and downward over the middle third.
4. Continues lowering into a long, more horizontal stretched shape.
5. Ends in a low, extended resting configuration.

Motion reading:

- This reads strongly as a settle/down/sleep-style motion.
- The important feature is the gradual transition through a middle posture before reaching the low rest pose.

## Video 08

- File: `08_20260425_043832_01.mp4`
- Duration: `39.6s`
- Contact sheet: `frame_exports/08_20260425_043832_01_contact.jpg`

Observed full motion process:

1. Starts facing a small tabletop interaction zone near the laptop and bottle.
2. The guest moves a hand/object across the right side of the workspace.
3. The robot tracks along the tabletop with continuous extension toward that side.
4. It holds the far-side target position with small local corrections.
5. Ends still oriented toward the target area rather than returning fully to center.

Motion reading:

- This is another strong tabletop/object-follow reference.
- Compared with Video 04, the follow path is longer and more clearly sustained across the workspace.

## Cross-video observations

- `03`, `04`, and `08` are the strongest references for hand/tabletop follow behavior.
- `02` is the strongest reference for cautious social approach with hesitation.
- `06` is a compact farewell reference.
- `07` is the cleanest settle/sleep reference.
- `01` is useful for a slow open/unfold structure, but the semantic read is weaker than the others if used alone.
- `05` appears expressive rather than precision-follow; it would benefit from denser sampling before being used as strict choreography truth.

## Suggested next analysis pass

If this needs to drive final script writing, the next useful step would be:

1. Export a denser set of frames for `05` and `01`.
2. Mark stage boundaries as `phase_01`, `phase_02`, etc.
3. Convert each video into a scriptable beat sheet:
   - start pose
   - transition pose
   - hold
   - micro-motion
   - recovery pose
