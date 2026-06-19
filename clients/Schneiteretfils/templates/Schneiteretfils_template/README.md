# Arsuno social post template

Place fixed template assets for Arsuno social exports in `assets/`.

Expected assets:

- `assets/logo.png` - transparent PNG logo used in the top-left template slot.

The text card is drawn by code from `template.json`, with the hardcoded
two-line text:

- `Build with AI` - bold
- `Fast and efficient` - regular

If `assets/logo.png` is not present, the renderer falls back to the workspace logo
at `clients/arsuno/logo.png` so the template can be tested before final assets are
provided.
