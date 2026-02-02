---
name: ue-sequence-fixer
description: Unreal Engine Sequence Fixer - Automates duplication, trimming, and asset repair for Line Sequences. Can clone a sequence, change its length, and attempt to auto-fix broken actor bindings.
---

# Unreal Engine Sequence Fixer

A utility skill to duplicate, trim, and repair Level Sequences in Unreal Engine 5.
It is useful when you want to create a shorter version of a long sequence (e.g., cut a 20min cinematics down to 10min) and automatically fix broken object bindings.

## Capabilities

- **Duplicate**: Clone an existing sequence to a new path.
- **Trim**: Set the playback end time to a specific duration (in minutes).
- **Auto-Fix**: Detect red (broken) object bindings and attempt to find actors with the same name in the current level to re-bind them.
- **Audit**: Report missing assets in tracks.

## Usage

When the user asks to "shorten", "trim", "fix", or "copy" a sequence, use the UE Python script.

**Important**: This skill requires the Unreal Engine Editor to be open and the Python plugin enabled. The script is run via the `unreal_engine_expert` context or directly if you have access to the UE Python command line.

Since OpenClaw runs outside UE, this skill generates the **Python Code Snippet** for the user to copy-paste into UE's Output Log, OR (if configured) runs it via a remote bridge.

### Command Pattern

If the user says: "Fix the bindings in /Game/Cinematics/MyBrokenSeq"

**Generate this Python command (In-place Fix):**

```python
import sys
import os

# Dynamic path resolution for OpenClaw standard install
# This works if the skill is installed in the default location on any machine
home_dir = os.path.expanduser("~")
script_path = os.path.join(home_dir, "clawd", "skills", "ue-sequence-fixer", "scripts")

if script_path not in sys.path:
    sys.path.append(script_path)

import sequence_repair_kit
import importlib
importlib.reload(sequence_repair_kit)


# Execute (source only = in-place repair)
fixer = sequence_repair_kit.SequenceRepairKit()
# When target is same as source (or None), it performs fix on original
fixer.process_sequence(
    source_path="/Game/Cinematics/MyBrokenSeq", 
    target_path="/Game/Cinematics/MyBrokenSeq" 
)
```

## Examples

> **User**: "My sequence 'LevelSequence_0' has broken bindings. Can you fix it?"
> **AI**: Generates code to repair `/Game/.../LevelSequence_0` in-place.

> **User**: "I copied a sequence to 'MyShortSeq' but everything is red. Fix it."
> **AI**: Generates code to repair `MyShortSeq`.

## Workflow (Step-by-Step)

Follow these steps to repair a sequence in your company project:

1.  **Open the Level**: In Unreal Engine, open the Level that acts as the context for the Sequence.
    *   *Why?* The script fixes broken bindings by searching for matching Actors in the *currently open world*.
2.  **Ask the Bot**: In Discord/Chat, ask:
    *   `@ue-sequence-fixer Fix the bindings in /Game/Path/To/YourSequence`
3.  **Run the Code**:
    *   The bot will generate a Python script block.
    *   **Copy** the entire block.
    *   Paste it into the **Unreal Engine Output Log** (ensure it's in Python mode) and hit Enter.
4.  **Verify**: Check the Output Log for "FIXED" messages and open your Sequence to confirm bindings are restored.
