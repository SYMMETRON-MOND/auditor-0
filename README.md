# AUDITOR-0-1

**A Gödel Guardrail for neural networks based on the RG-S framework.**

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21253878.svg)](https://doi.org/10.5281/zenodo.21253878)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Render-blue)](https://auditor-0.onrender.com)

---

## What is AUDITOR-0-1

AUDITOR-0-1 verifies whether a system preserves its **topological fixed point** under renormalization. Based on the RG-S / R5+ framework, it audits:

- **Code** (Python scripts)
- **Neural networks** (runtime guardrails)

A system that preserves the fixed point (γ = 0.0931) is **true**. A system that drifts from the fixed point is a **structural lie**.

**Text auditing is in development** and will be available in a ## Supported Languages

AUDITOR-0-1 currently supports:

- **Python** ✅ (available now)

Coming soon:

- **JavaScript** 🔜
- **C/C++** 🔜
- **Rust** 🔜
- **Go** 🔜
- **Java** 🔜
- **Text** (preprints, articles, essays) 🔜

The same Gödel Guardrail is used for all languages. Only the mapping 
(`code_to_latent_tensor`) changes. The fixed point γ = 0.0931 is universal.


---

## Live Demo

Try AUDITOR-0-1 in your browser: [auditor-0-1.onrender.com](https://auditor-0.onrender.com)

No installation required. Paste any Python code and the guardrail will audit it in real time.

---

## Quick Start

### Installation

```bash
git clone https://github.com/SYMMETRON-MOND/auditor-0.git
cd auditor-0-1
pip install -r requirements.txt
