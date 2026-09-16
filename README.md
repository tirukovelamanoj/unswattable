# Unswattable

Try to swat a fruit fly. It dodges you using a real connectome, simulated live in
the browser.

The escape circuit is traced from FlyWire FAFB v783: looming detectors (LC4,
LPLC2) converge on the giant fiber (DNp01) and the steering neuron (DNa02),
exactly as published. Nothing sits between the spikes and the movement, so when
you silence a population with the lesion buttons the fly genuinely goes blind to
you.

It also learns. The mushroom body (900 Kenyon cells, 96 MBONs, 150 dopaminergic
neurons) conditions on the direction you keep attacking from, via the real
plasticity rule: a Kenyon cell active at the same time as dopamine has that
synapse depressed. The dial in the corner is drawn straight from those weights.

## Numbers

| | |
|---|---|
| neurons | 1,984 |
| synapses | 17,716 |
| plastic (KC to MBON) | 3,988 |
| model | leaky integrate and fire, 9 ms brain time per frame |

## Run it

Needs a server, not a file:// open, because it fetches `flydata.json`.

    python3 -m http.server 8000
    # http://localhost:8000

## Deploy

Three files, entirely static, no build step: `index.html`, `flydata.json`
and `og.png` (link preview). Any static host works, no build command, output
directory is the repo root.

Deployed at https://fly.manojtirukovela.com on Cloudflare Pages: no build
command, output directory is the repo root. The `og:image`, `twitter:image` and
`og:url` meta tags are absolute against that host, so change them if the domain
moves.

## What is real and what is not

Real: every neuron, every synapse, the synapse counts, the excitatory and
inhibitory signs from predicted neurotransmitters, and the topology.

Also real, and worth knowing about: the looming detectors receive an efference
copy, so the optic flow the fly generates by its own flight is largely cancelled
before it reaches them. This is why it can fly straight past a motionless cursor
without reacting, but bolts from one that moves. Flies do exactly this, using a
corollary discharge of their own motor commands.

Modelled, and labelled as such in the code and in the page footer:

- Receptive fields are approximated from each neuron's position in its optic
  lobe. Real retinotopy is measured, not inferred from soma position.
- Kenyon cells are driven by a direction code. Real Kenyon cells encode odour.
- Learned danger raises the looming gain. In the connectome the only mushroom
  body output reaching this circuit is MBON31/32 onto DNa02, which steers; no
  MBON touches DNp01, so a learned change cannot alter the escape threshold
  through real wiring.
- Flight speed, drag and saccade timing are tuned game physics downstream of the
  brain's decision.

## Data

FlyWire FAFB v783, Dorkenwald et al., Nature 2024, CC-BY.
Rebuild `flydata.json` with `build_data.py` (needs the FlyWire annotation TSV and
the v783 connection table).
