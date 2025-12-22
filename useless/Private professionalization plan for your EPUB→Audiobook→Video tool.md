# Professional plan for your private EPUB→Audio→Video pipeline
Goals
* Make the project reliable, fast, and easy to run for you only \(no GitHub\)\.
* Reduce failures with Edge‑TTS, keep Piper smooth, and protect RAM/disk\.
* Keep the UI simple\. Only add options that remove pain\.
Current state \(very good foundation\)
* End‑to‑end flow works: EPUB → TTS → mix → video → description → history\.
* Batch range selection, cover extraction, banned‑word filter, pronunciation fixes, cleanup\.
* Windows‑friendly \(batch launcher, Piper bundled, models present\)\.
Key gaps to close
* Some config fields are documented but not enforced \(edge\_tts\_request\_delay, system\_limits, min\_audio\_size\_mb\)\.
* Background music path is hardcoded in code instead of using config\.
* Piper binary not auto‑detected from local piper\\piper\.exe\.
* Log file grows forever\. Temp folder sometimes holds 0‑byte clips\.
* Large concatenations can spike memory; concurrency can trigger Edge‑TTS 403\.
* Folder naming inconsistent \(Active vs Nonactive/Uploaded\)\.
Roadmap \(phased\)
Phase 0 — Safety and bug fixes \(low risk, quick\)
* Use configured background\_music\_path in create\_video\.
* Deep‑copy defaults during config validation \(avoid hidden mutations\)\.
* Piper fallback: if PATH check fails, auto‑use piper\\piper\.exe\.
* Apply edge\_tts\_request\_delay \(sequential sleep \+ concurrent staggering\)\.
* Rotate logs to cap file size; auto‑purge 0‑byte temp mp3s\.
Phase 1 — Reliability and resource control
* Enforce system\_limits: warn/confirm when chapters per video exceed max\_batch\_size; RAM warning if psutil is present\.
* Low‑memory audio assembly option: ffmpeg concat demuxer \(no in‑RAM merge\) for big batches\.
* Auto chunk very long chapters into smaller pieces before TTS \(protect engines\)\.
* “Retry failed only” rerun: offer reprocessing failed chapters with same or fallback engine \(e\.g\., switch to Piper\)\.
* Disk‑space preflight: warn before starting if free space is too low\.
Phase 2 — Usability and speed
* Non‑interactive flags \(optional\): \-\-engine, \-\-voice, \-\-range, \-\-batch\-size, \-\-concurrent yes|no; keep prompts as default\.
* Per‑book profile file \(book\_profile\.json in project root\) to remember last engine/voice/speed\.
* Preflight summary screen with risk tips \(based on engine, batch size, and delay\)\.
* Duplicate EPUB detection \(hash\) in global history to skip already processed books\.
Phase 3 — Output quality and packaging
* Thumbnail text overlay \(optional\): put book name and chapter range on the generated cover\.
* Optional loudness normalization pass using ffmpeg loudnorm for consistent volume\.
* Add chapter markers into the MP4 \(or keep only in description if you prefer simple\)\.
* Personal packaging: build a single \.exe with PyInstaller for your machine\.
Phase 4 — Structure and housekeeping \(only if you want\)
* Split the big script into small files: config\.py, epub\_io\.py, tts\.py, audio\.py, video\.py, ui\.py, utils\.py\. This is optional; functionally you’re fine today\.
* Unify folders: Novels/Active Novels for in‑progress, Novels/Uploaded \(or Archived\) for finished\. Update constants accordingly\.
Concrete changes with file pointers
* Background music path
    * epub\_project\_manager\.py \(1518–1591\): use CONFIG\["audio\_settings"\]\["background\_music\_path"\] instead of "background\.mp3"\.
* Config deep‑copy \+ enforcement
    * epub\_project\_manager\.py:216–283 validate\_config → switch to deepcopy; enforce min\_audio\_size\_mb, system\_limits, and warnings for invalid regex\.
* Piper detection fallback
    * epub\_project\_manager\.py:115–127 \(PIPER\_AVAILABLE check\) and 1040–1060 \(piper\_cmd\): detect piper\\piper\.exe; add audio\_settings\.piper\_exe\_path; use it when building the command\.
* Edge‑TTS delay
    * epub\_project\_manager\.py:1274–1320 and 1120–1160: stagger concurrent starts \(await sleep based on index\); add small sleep per chapter in sequential when engine==edge\.
* Log rotation
    * epub\_project\_manager\.py:62–71 logging setup → replace with RotatingFileHandler \(2 MB × 3 backups\) and same console output\.
* Temp hygiene
    * Before assembly in run\_audio\_gen\_with\_timestamps \(around 1422–1451\), delete \*\.mp3 <1 KB in temp; log count removed\.
* Enforce system\_limits
    * epub\_project\_manager\.py:1829–1862 \(after computing batches\): if any batch size > CONFIG\.system\_limits\.max\_batch\_size, show warning and require confirmation\.
* RAM warning \(optional if psutil present\)
    * New helpers near 354–375: check\_available\_ram\(\), warn\_if\_low\_ram\(\); call early in main\(\) after banner\.
* Low‑memory assembly mode \(ffmpeg concat\)
    * Alternative to concatenate\_audioclips at 1431–1436: write a concat\_list\.txt of chapter mp3s and call ffmpeg concat demuxer to produce final file, then clean list\.
* Auto chunk long chapters
    * In sequential and concurrent generation paths \(1327–1369, 1124–1147\): if text length exceeds threshold, split by paragraphs into smaller clips and join\.
* Retry failed only
    * After a run where success\_rate < 100% or failed\_chapters non‑empty \(1407–1420\): prompt to reprocess failed items, with option to switch engine; skip successful clips\.
* Folder naming
    * Constants at 148–151: change UPLOADED\_NOVELS\_DIR to "Archived Novels" or match your existing "Nonactive Novels"; add move on “Mark complete?” prompt at end of main\.
* Duplicate EPUB detection
    * HISTORY\_FILE already exists\. Add EPUB file hash to history; if seen, offer to open the existing project instead of creating a new one\.
* Per‑book profile
    * Save a small JSON under project root with chosen engine/voice/speed; load it next time to pre‑fill menu\.
Rollout plan
* Implement Phase 0 first and test on a small 5–10 chapter batch\.
* Enable system\_limits and RAM warning; test one medium batch \(20–30 chapters\)\.
* Only add ffmpeg concat and chunking if you hit memory/time issues on very large batches\.
* Keep everything interactive by default; non‑interactive flags are optional\.
Verification plan
* For each change, run a 2–3 chapter smoke test and check: audio exists, duration non‑zero, video renders, description saved, history entry written\.
* Stress test Edge‑TTS with small delay and concurrent=3; confirm no 403; if 403 seen, increase delay\.
* Confirm logs rotate and temp files are cleaned\.
Non‑goals
* No online services, no accounts, no public repository\.
* No mandatory new dependencies except optional psutil; ffmpeg already comes via imageio‑ffmpeg\.
What I need from you
* Choose the folder naming you want for “finished” books \(Uploaded in Youtube vs Nonactive Novels vs Archived Novels\)\.
* Confirm whether you want RAM warnings \(psutil\) and low‑memory ffmpeg concat to be enabled by default\.
* Confirm whether to add non‑interactive CLI flags now or later\.
Ready to execute
* If you approve, I’ll implement Phase 0 and the system\_limits warnings from Phase 1 in a single pass, keeping edits minimal and safe\.
