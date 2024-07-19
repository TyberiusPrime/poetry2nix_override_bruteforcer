#!/usr/bin/env python
from pathlib import Path
import sys
import shutil
from shared import examine_results
import shared


if __name__ == "__main__":
    count, classified = examine_results()

    for k, v in sorted(count.items(), key=lambda x: x[1], reverse=True):
        print(k, v)

    total = sum(count.values())
    print("total", total, len(classified))
    corrected_total = (
        sum(count.values())
        - count["missing:not-done"]
        - count["fail:expected-manual"]
        - count["fail:expected-autodetected"]
    )
    print("corrected total", corrected_total)
    print(
        "% without patch",
        "%.2f" % (100 * count["success:upstream"] / corrected_total),
        "(%.2f)" % (100 * count["success:upstream"] / total),
    )
    print(
        "% after patch",
        "%.2f"
        % (
            100
            * (count["success:upstream"] + count["success:needed_patch"])
            / corrected_total
        ),
        "(%.2f)"
        % (100 * (count["success:upstream"] + count["success:needed_patch"]) / total),
    )
