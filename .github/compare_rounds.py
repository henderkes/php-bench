#!/usr/bin/env python3
"""Round-over-round stability check for the cpu suite.

Usage: compare_rounds.py <round1_dir> <round2_dir> [...] <final_dir>

Each round dir holds one hyperfine-export JSON per target
(cpu-official-8.6-cli-bookworm.json = NTS build,
 cpu-official-8.6-zts-bookworm.json = shipped GA ZTS image).
Per script:variant: the ZTS-vs-NTS overhead of every round, the spread
across rounds, and the median. STABLE when spread <= 1.5 pts
(0.5 for hash).
"""
import json, sys, os, statistics

def collect(d):
    arms = {}
    for fname in os.listdir(d):
        if not fname.endswith(".json"):
            continue
        arm = "nts" if "-cli-" in fname else ("zts" if "-zts-" in fname else None)
        if arm is None:
            continue
        for r in json.load(open(os.path.join(d, fname)))["results"]:
            arms[(r["command"], arm)] = r["mean"] * 1000
    return arms

def main():
    rounds = [collect(d) for d in sys.argv[1:]]
    labels = sorted(set.intersection(*[set(r) for r in rounds]))
    bad = []
    print("\n## Round stability (NTS-vs-ZTS overhead per round, " + str(len(rounds)) + " rounds)\n")
    print("| script:variant | " + " | ".join(f"r{i+1}" for i in range(len(rounds))) + " | spread | median | verdict |")
    print("| --- | " + " | ".join("---:" for _ in range(len(rounds) + 3)) + " |")
    for label in labels:
        ovh = [(r[(label, "zts")] / r[(label, "nts")] - 1) * 100 for r in rounds]
        spread = max(ovh) - min(ovh)
        thr = 0.5 if label.startswith("hash") else 1.5
        ok = spread <= thr
        if not ok:
            bad.append(label)
        print("| " + label + " | " + " | ".join(f"{o:+.1f}%" for o in ovh) + f" | {spread:.1f} pts | {statistics.median(ovh):+.1f}% | {'STABLE' if ok else 'UNSTABLE'} |")
    print(f"\n{len(labels) - len(bad)}/{len(labels)} labels stable across all {len(rounds)} rounds.\n")
    if bad:
        print("Unstable labels: " + ", ".join(bad))

if __name__ == "__main__":
    main()
