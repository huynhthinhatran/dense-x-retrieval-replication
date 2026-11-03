"""Compare our replication results with the original numbers of Dense X Retrieval (Chen et al., 2024).

Reads the files in results/ and writes:
  - results/paper_vs_ours.csv : paper numbers and ours side by side (Tables 3/4/5, NQ and SQuAD columns)
  - results/trend_summary.csv : number of cells that keep the trend, per table

Usage: python analysis/compare_with_paper.py   (from the repo root)
"""
from pathlib import Path
import pandas as pd

RES = Path(__file__).resolve().parent.parent / "results"
RETRIEVERS = ["SimCSE", "Contriever", "DPR", "GTR"]
GRANS = ["passage", "sentence", "proposition"]

# Paper numbers (arXiv 2312.06648), NQ and SQuAD columns only.
# Order in each list: passage, sentence, proposition
PAPER = {
    "table3": {  # Passage Recall
        ("NQ", "R@5"):   {"SimCSE": [28.8, 35.5, 41.1], "Contriever": [42.5, 46.4, 50.1], "DPR": [66.0, 66.0, 65.4], "GTR": [66.3, 66.4, 66.5]},
        ("NQ", "R@20"):  {"SimCSE": [44.3, 53.1, 58.9], "Contriever": [63.8, 66.8, 70.0], "DPR": [78.0, 78.0, 77.7], "GTR": [78.4, 79.4, 79.6]},
        ("SQUAD", "R@5"):  {"SimCSE": [29.5, 37.1, 38.7], "Contriever": [40.8, 45.1, 50.7], "DPR": [38.3, 40.3, 41.4], "GTR": [54.4, 60.9, 63.3]},
        ("SQUAD", "R@20"): {"SimCSE": [45.5, 52.3, 53.9], "Contriever": [59.8, 63.5, 67.7], "DPR": [53.9, 55.9, 57.2], "GTR": [68.1, 73.4, 75.0]},
    },
    "table4": {  # FiD EM
        ("NQ", "EM@top5"):  {"SimCSE": [16.6, 20.7, 24.5], "Contriever": [23.2, 26.0, 28.9], "DPR": [41.1, 40.3, 39.7], "GTR": [39.8, 39.4, 40.0]},
        ("NQ", "EM@top20"): {"SimCSE": [23.6, 28.1, 33.1], "Contriever": [35.1, 36.8, 39.2], "DPR": [45.6, 45.6, 45.2], "GTR": [46.1, 45.9, 46.9]},
        ("SQUAD", "EM@top5"):  {"SimCSE": [14.6, 19.6, 21.4], "Contriever": [23.9, 26.7, 30.8], "DPR": [18.8, 21.1, 22.2], "GTR": [29.9, 35.7, 37.8]},
        ("SQUAD", "EM@top20"): {"SimCSE": [20.7, 25.8, 27.6], "Contriever": [32.7, 34.7, 37.6], "DPR": [25.4, 27.4, 28.3], "GTR": [35.1, 39.1, 40.4]},
    },
    "table5": {  # LLaMA-2-7B EM@l tokens
        ("NQ", "EM@100"):  {"SimCSE": [20.5, 21.1, 22.0], "Contriever": [24.5, 25.0, 25.8], "DPR": [30.6, 32.5, 31.5], "GTR": [30.0, 30.9, 32.1]},
        ("NQ", "EM@500"):  {"SimCSE": [22.9, 24.3, 26.0], "Contriever": [28.7, 30.2, 30.3], "DPR": [33.7, 34.1, 33.8], "GTR": [33.9, 34.0, 33.8]},
        ("SQUAD", "EM@100"): {"SimCSE": [13.7, 17.7, 18.6], "Contriever": [17.7, 22.5, 24.8], "DPR": [14.2, 17.6, 18.2], "GTR": [21.5, 29.8, 32.5]},
        ("SQUAD", "EM@500"): {"SimCSE": [16.6, 21.5, 22.7], "Contriever": [24.2, 28.1, 29.7], "DPR": [18.9, 22.1, 22.6], "GTR": [27.4, 31.7, 33.1]},
    },
}
FILES = {"table3": "table3_recall.csv", "table4": "table4_fid_em.csv", "table5": "table5_em.csv"}


def load_ours(name):
    df = pd.read_csv(RES / FILES[name])
    df = df.rename(columns={df.columns[0]: "retriever", df.columns[1]: "granularity"})
    return df[df.granularity.isin(GRANS)].set_index(["retriever", "granularity"])


def main():
    rows = []
    for table, cols in PAPER.items():
        ours = load_ours(table)
        for (ds, metric), by_ret in cols.items():
            col = f"{ds} {metric}"
            for ret in RETRIEVERS:
                p = dict(zip(GRANS, by_ret[ret]))
                o = {g: float(ours.loc[(ret, g), col]) for g in GRANS}
                rows.append({
                    "table": table, "dataset": ds, "metric": metric, "retriever": ret,
                    **{f"paper_{g}": p[g] for g in GRANS},
                    **{f"ours_{g}": o[g] for g in GRANS},
                    "paper_Δprop-pass": round(p["proposition"] - p["passage"], 1),
                    "ours_Δprop-pass": round(o["proposition"] - o["passage"], 1),
                    "paper_strict": p["proposition"] > p["sentence"] > p["passage"],
                    "ours_strict": o["proposition"] > o["sentence"] > o["passage"],
                    "ours_prop>pass": o["proposition"] > o["passage"],
                    "same_sign_as_paper": (p["proposition"] - p["passage"] > 0) == (o["proposition"] - o["passage"] > 0),
                })
    df = pd.DataFrame(rows)
    df.to_csv(RES / "paper_vs_ours.csv", index=False)

    summ = []
    for (table, ds), g in df.groupby(["table", "dataset"], sort=False):
        summ.append({"table": table, "dataset": ds, "cells": len(g),
                     "ours Prop>Sent>Pass": int(g.ours_strict.sum()),
                     "paper Prop>Sent>Pass": int(g.paper_strict.sum()),
                     "ours Prop>Pass": int(g["ours_prop>pass"].sum()),
                     "same sign Δ as paper": int(g.same_sign_as_paper.sum())})
    for table, g in df.groupby("table", sort=False):
        summ.append({"table": table, "dataset": "ALL", "cells": len(g),
                     "ours Prop>Sent>Pass": int(g.ours_strict.sum()),
                     "paper Prop>Sent>Pass": int(g.paper_strict.sum()),
                     "ours Prop>Pass": int(g["ours_prop>pass"].sum()),
                     "same sign Δ as paper": int(g.same_sign_as_paper.sum())})
    s = pd.DataFrame(summ)
    s.to_csv(RES / "trend_summary.csv", index=False)
    print(s.to_string(index=False))

    # McNemar: number of cells where proposition significantly beats passage
    for f, label in [("mcnemar_win_loss.csv", "Retrieval Recall"), ("table4_fid_mcnemar.csv", "FiD EM")]:
        m = pd.read_csv(RES / f)
        m = m[m["compare"] == "proposition vs passage"]
        sig_win = ((m["McNemar p"] < 0.05) & (m["Δ (pp)"] > 0)).sum()
        sig_loss = ((m["McNemar p"] < 0.05) & (m["Δ (pp)"] < 0)).sum()
        print(f"{label}: proposition vs passage — significant wins {sig_win}/{len(m)}, significant losses {sig_loss}/{len(m)}")


if __name__ == "__main__":
    main()
