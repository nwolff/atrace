# To record an animation for later playback

(The commands shown are an example)

## 1. Play the trace and adapt the terminal size

    uv run -m atrace.animated_histogram examples/fizzbuzz.py

## 2. Capture an asciinema trace

    uv run asciinema rec \
    -c "python3 -m atrace.animated_histogram examples/fizzbuzz.py" \
    local/fizzbuzz.cast --overwrite

## 3. Check that you like it

    asciinema play local/fizzbuzz.cast

## 4. Convert to GIF

You need to install agg first (with apt, brew, etc.).
Then:

    agg --no-loop local/fizzbuzz.cast local/fizzbuzz.gif

# Failed experiments

- Tried rich.save_svg, it generates a long strip of console output instead of an
  animation
- Tried termtosvg, it's easy to use but give glitchy output
- asciinema is cool
- Capture the animation with Ascii-cinema / moviepy
