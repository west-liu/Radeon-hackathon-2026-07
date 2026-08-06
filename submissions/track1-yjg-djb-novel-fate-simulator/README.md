# Novel Fate Simulator

**Track:** Track 1 - Development of Multimodal Content Creation Tools  
**Applicant:** `yjg-djb` (working placeholder; replace with the registered team or applicant name)  
**Submission status:** Draft - required deliverables are still being completed.

## Project Overview

Novel Fate Simulator is an AI-powered dynamic narrative world simulator. A user
uploads a novel, selects a key character, and enters a world that remains
anchored to the source material while responding to the user's choices. The
system is designed to update character destinies, faction relationships, and
the wider world order rather than generate an isolated chat or a fixed
branching story.

The intended experience is: "I entered this fictional world, and this is how
the world changed because of me."

## Target Users and Scenarios

- Readers who want to enter and reshape a novel they care about.
- Interactive-fiction and romance-game players who want both emotional
  immersion and meaningful freedom.
- TRPG, Dungeons & Dragons, and text role-playing players who value persistent
  world simulation.

## Core Experience

1. The user uploads a novel.
2. AI extracts its world model, central conflicts, rules, factions, key
   characters, and three to five persistent fate anchors.
3. The user selects a character and receives an initial identity, situation,
   world issue, and stage objective.
4. Each interaction updates the structured world state and produces a new
   narrative scene.
5. Every five to eight turns, the system performs a fate review and gradually
   shifts objectives based on accumulated choices.
6. When the central conflict, key character destinies, and faction landscape
   have sufficiently converged, the user may conclude the story or continue.
7. The system generates a world ending, character ending, relationship
   outcomes, and a summary of deviations from the source novel.

## Proposed Architecture

The design combines a structured world-state engine with a constrained AI
narrative interface:

- **World-issue layer:** central conflict, world rules, unstable factors, and
  convergence status.
- **Faction layer:** faction strength, alliances, hostility, and control of key
  power nodes.
- **Character-fate layer:** player identity, influence, relationships, and the
  evolving fate of important non-player characters.
- **Canon-anchor layer:** source-material events and conflicts that retain
  weight even when their outcomes are rewritten.
- **Objective layer:** persistent goals, current goals, and behavior-derived
  secondary goals.
- **Narrative layer:** scenes and dialogue generated from the current state,
  character identity, and canon anchors.
- **Closure evaluator:** evaluates world convergence and enables a meaningful
  ending instead of an arbitrary cutoff.

The full product concept includes text, generated scene illustrations, and
voice. The first MVP focuses on text narration and generated illustrations;
voice is planned for a later iteration.

## AMD Radeon / ROCm Adaptation

The AMD Radeon GPU / ROCm execution path, model configuration, performance
measurements, and reproducible evidence have not yet been added. No Radeon or
ROCm performance claim is made in this draft.

## Current Materials

- [Original product design document in Chinese](product_design_zh.pdf)

## Required Materials Still Pending

- English project profile PDF.
- Complete public source-code repository and setup README.
- AMD Radeon GPU / ROCm adaptation and execution evidence.
- A 3-5 minute demo video showing the real workflow and Radeon execution.
- A supplementary presentation or poster.
- Reproduction steps, dependency versions, and validation results.

## Reproducibility

Reproduction instructions will be added together with the public source-code
repository. This draft should not yet be treated as a reproducible or complete
competition submission.
