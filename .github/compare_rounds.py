#!/usr/bin/env python3
"""Round-over-round stability check for the cpu suite.

Usage: compare_rounds.py <round1_dir> <round2_dir>

Each round dir holds one hyperfine-export JSON per target
(cpu-official-8.6-cli-bookworm.json = NTS build,
 cpu-official-8.6-zts-bookworm.json = shipped GA ZTS image).
Prints per script:variant the ZTS overhead measured in each round and the
round-to-round drift; a label is STABLE when the rounds agree within
1.5 points (0.5 for hash).
"""
import json, sys, os

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
    r1, r2 = collect(sys.argv[1]), collect(sys.argv[2])
    labels = sorted({k[0] for k in r1} & {k[0] for k in r2})
    bad = []
    print("\n## Round stability (NTS-vs-ZTS overhead per round)\n")
    print("| script:variant | r1 overhead | r2 overhead | drift | verdict |")
    print("| --- | ---: | ---: | ---: | --- |")
    for label in labels:
        o1 = (r1[(label, "zts")] / r1[(label, "nts")] - 1) * 100
        o2 = (r2[(label, "zts")] / r2[(label, "nts")] - 1) * 100
        drift = abs(o1 - o2)
        thr = 0.5 if label.startswith("hash") else 1.5
        ok = drift <= thr
        if not ok:
            bad.append(label)
        print(f"| {label} | {o1:+.1f}% | {o2:+.1f}% | {drift:.1f} pts | {'STABLE' if ok else 'UNSTABLE'} |")
    print(f"\n{len(labels) - len(bad)}/{len(labels)} labels stable across rounds.\n")
    if bad:
        print("Unstable labels: " + ", ".join(bad))

if __name__ == "__main__":
    main()
