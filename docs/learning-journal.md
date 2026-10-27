# SwarmGesture — Learning Journal

## Weeks 1–2 | 14–27 October 2026

### Progress
- Started the project and wrote the first plan, requirements and work packages (**MS1–MS2**).
- Installed and tested **MediaPipe**. Our `hand_tracker.py` shows 21 hand landmarks live through the webcam (**W01 — done**).
- Visited the drone lab with the professor and **3D printed propeller protectors** for the Crazyflies (**W11 — preparation**).
- Started a tool to record labeled hand-landmark data. We collected about **108 open-palm samples** in `palm.csv` (**W02/W04 — in progress**).

### What we learned / challenges
- MediaPipe finds the hand joints, but we still need our **own model** to recognize gestures.
- We need examples of each gesture from different people and angles. Samples from one recording are not enough to test accuracy reliably.

### Decisions
- Train a gesture classifier using **21 landmarks (63 coordinates)** instead of raw camera images. Start with our own recordings and consider a public dataset such as HaGRID later.
- Test in simulation before trying the real drones.

### Next steps
- Record the other five gestures and collect samples from more people (**W02/W04**).
- Build a simple rule-based baseline and train a first classifier (**W03/W04**).
- Check the printed protectors and begin setting up the drone simulation (**W06/W11**).
