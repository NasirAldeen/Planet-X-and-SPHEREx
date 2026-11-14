export function parseCoordinate(text, isRA = false) {
  const raw = String(text).trim().replaceAll('−', '-');
  if (!raw) throw Error('Enter both sky coordinates.');
  let value;
  if (/^[+-]?(?:\d+\.?\d*|\.\d+)$/.test(raw)) value = Number(raw);
  else {
    const parts = raw.match(/^([+-]?\d{1,3})(?:[:hHdD°\s]+)(\d{1,2})(?:[:mM′'\s]+)(\d{1,2}(?:\.\d+)?)(?:[sS″"])?$/);
    if (!parts) throw Error('Use decimal degrees or three parts, such as 17:57:48.5 and +04:46:05.5.');
    const [, a, b, c] = parts;
    if (+b >= 60 || +c >= 60) throw Error('Minutes and seconds must be less than 60.');
    value = (Math.abs(+a) + +b / 60 + +c / 3600) * (a.startsWith('-') ? -1 : 1) * (isRA ? 15 : 1);
  }
  if (!Number.isFinite(value) || (isRA ? value < 0 || value >= 360 : Math.abs(value) > 90))
    throw Error(isRA ? 'Right ascension must be from 0° to less than 360°.' : 'Declination must be between −90° and +90°.');
  return value;
}

export function matchedFrames(frames, reference, enabled) {
  if (!enabled) return frames.map((_, i) => i);
  const wave = frames[reference]?.wavelength_um;
  if (!(wave > 0)) return [reference];
  return frames.flatMap((frame, i) => frame.wavelength_um > 0 &&
    Math.abs(frame.wavelength_um / wave - 1) <= .05 + 1e-10 ? [i] : []);
}

export function percentile(values, p) {
  if (!values.length) return 1;
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.min(sorted.length - 1, Math.floor((sorted.length - 1) * p))];
}

export function sharedScale(frames) {
  const sample = [];
  for (const frame of frames) {
    const step = Math.max(1, Math.floor(frame.pixels.length / 3000));
    for (let i = 0; i < frame.pixels.length; i += step) {
      if (frame.pixels[i] !== null && Number.isFinite(frame.pixels[i])) sample.push(frame.pixels[i]);
    }
  }
  const low = percentile(sample, .08);
  return {low, high: Math.max(low + .000001, percentile(sample, .997))};
}

export function difference(a, b) {
  return a.map((v, i) => v === null || b[i] === null ? null : v - b[i]);
}

export function stack(frames) {
  if (!frames.length) return [];
  return frames[0].pixels.map((_, i) => {
    let sum = 0, count = 0;
    for (const frame of frames) if (frame.pixels[i] !== null && Number.isFinite(frame.pixels[i])) {
      sum += frame.pixels[i]; count++;
    }
    return count ? sum / count : null;
  });
}

export function fieldURL(base, query) {
  const url = new URL(base);
  url.search = '';
  for (const [key, value] of Object.entries(query)) if (value !== undefined && value !== null) url.searchParams.set(key, value);
  url.hash = 'observatory';
  return url.href;
}
