# realtek-alc245-linux-fix

Realtek ALC245 Linux Fix (Unsolicited / Button Events)

This repository documents and experiments with undocumented Realtek ALC245
behavior observed on certain OEM laptops (HP, etc.), where media / jack /
button events work correctly on Windows but behave inconsistently or not at all
on Linux.

Problem Summary

- Button / media / jack related events:
  - Trigger randomly ("ghost presses")
  - Trigger without physical input
  - Not working
- Windows driver handles this correctly
- Linux HDA driver receives incomplete or incorrect unsolicited events

Hypothesis

The Windows Realtek driver sends undocumented HDA verbs or GPIO operations
that are not currently implemented or triggered in Linux.

Status

🟡 Research / reverse engineering 
