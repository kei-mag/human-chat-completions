# <img src="https://github.com/kei-mag/human-chat-completions/blob/main/src/assets/icon.png?raw=true" height="50" style="vertical-align: bottom;"> Human Chat Completions

&thinsp; [日本語](README.md) / **English** &emsp;&emsp; [![Release](https://github.com/miyamoto-hai-lab/human-chat-completions/actions/workflows/release.yml/badge.svg)](https://github.com/miyamoto-hai-lab/human-chat-completions/actions/workflows/release.yml)

Human Chat Completions is a desktop chat application designed for Wizard of Oz (WoZ) experiments, built with [Flet](https://flet.dev).

![Preview Clip](preview_clip.gif)

It provides an API endpoint compatible with OpenAI's `v1/chat/completions`. Instead of automatically returning an AI response, it routes the request to a Flet-based GUI where a human operator acts as the "Assistant".

Crucially, this tool features an LLM Copilot: it can automatically generate a draft response using a real LLM (e.g., GPT-5), which the operator can then edit, refine, or approve before sending it back to the user.

By default, the LLM handles all responses, allowing you to intervene only when necessary.
This gives you the flexibility to **seamlessly switch between purely human responses, human-edited AI drafts, and fully automated AI generation**.

## Features
- **API Compatibility**: Fully compatible with OpenAI's POST /v1/chat/completions format. Point your existing apps here to switch from AI to Human.
- **Flet GUI**: A clean, cross-platform dashboard (Web, macOS, Windows, Linux) for the operator.
- **LLM Copilot**:
    - The system generates a candidate response using a real LLM.
    - The human operator can use the draft as-is, edit it to correct errors/hallucinations, or rewrite it entirely.
- **Streaming Support**: Supports `stream: true`. The operator's typing is streamed to the client in real-time.
- **Experiment Logging**: Saves the user input, the initial AI draft, and the final human-edited response for analysis.

## Use Cases
1. **Wizard of Oz Studies**: Validate chatbot UX flows before finalizing the logic.
2. **RLHF Data Collection**: Create high-quality datasets by having humans correct AI errors in real-time.
3. **Safety & Alignment Testing**: Manually intervene when the AI generates unsafe content to test client-side guardrails.

## Installation
Download the executable file for your OS from the [Latest Release](https://github.com/miyamoto-hai-lab/human-chat-completions/releases/latest). For Windows, it is an installer, so follow the wizard to complete the installation.
