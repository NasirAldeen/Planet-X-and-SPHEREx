/** Editorial copy for each target. Every claim here is taken from the project's research paper
 *  (Research/Paper/SPHEREx_Research_Paper.md) or the supplied challenge text. */

export type TargetCopy = {
  id: string;
  lede: string;
  body: string[];
  caution: string;
  refs: string[]; // ids from references.json
  /** An image from another telescope, shown for context and never as a SPHEREx frame. */
  context?: { src: string; alt: string; caption: string };
  color: string;
};

export const COPY: Record<string, TargetCopy> = {
  barnard: {
    id: "barnard",
    lede: "The fastest-moving star in our sky, and a test of whether a shift smaller than one pixel can be seen.",
    body: [
      "Barnard's Star slides across the sky by about 10.4 arcseconds every year. Half a year later it has moved roughly 5.2 arcseconds, which is less than one SPHEREx pixel (6.15 arcseconds).",
      "That makes it a registration test: the motion only shows up when every frame is aligned to the same sky grid and compared against stationary stars.",
    ],
    caution:
      "The bright core can be flagged as saturated or unreliable. A planet proposed around this star was later challenged, and this viewer makes no claim about it.",
    refs: ["R01", "R10", "R13"],
    color: "#ff7a45",
  },
  "epsilon-indi": {
    id: "epsilon-indi",
    lede: "A pair of brown dwarfs, Ba and Bb, orbiting the star Epsilon Indi A.",
    body: [
      "Brown dwarfs are balls of gas too massive to be planets and too light to burn like stars. This pair drifts about 2.35 arcseconds in half a year.",
      "SPHEREx cannot split the two. The viewer follows the system as one blended point, not two separate objects.",
    ],
    caution: "Do not read masses or separate brightnesses off these frames. The planet in this system belongs to the primary star, not to Ba or Bb.",
    refs: ["R03"],
    color: "#7fa2ff",
  },
  "wise-0855": {
    id: "wise-0855",
    lede: "One of the coldest known brown dwarfs, and one of the fastest movers in the sky.",
    body: [
      "WISE 0855 travels about 8.1 arcseconds per year, roughly 4.05 arcseconds in half a year. It is extremely faint in the near-infrared.",
      "Its position here is the coordinate supplied with the challenge: 08h 55m 10.831s, −07° 14′ 42.53″.",
      "The frames above look like static because the signal here is tiny. The brightest 1% of pixels reach about 0.2 MJy/sr, against 4 to 7 for Barnard's Star, so a single exposure is mostly noise. Stack averages all 18 frames to push the noise down.",
    ],
    context: {
      src: "/docs/PIA18002.jpg",
      alt: "False-colour infrared image from NASA's WISE telescope, labelled May 2010, showing several blue-white sources",
      caption:
        "For context: this region as imaged by NASA's WISE telescope in May 2010, a still from a NASA/JPL animation of the discovery. It is a false-colour public image from a different telescope, not a SPHEREx frame. Credit: NASA/JPL-Caltech/Penn State University.",
    },
    caution: "Seeing nothing at this position is a valid result. A faint dot nearby must not be matched to it just because it looks plausible.",
    refs: ["R04", "R19"],
    color: "#c18cff",
  },
  "rw-aurigae": {
    id: "rw-aurigae",
    lede: "A young star system whose light has dimmed and brightened over the years.",
    body: [
      "RW Aurigae is still forming. Published measurements show its brightness changing by large amounts, so the question here is variability, not motion.",
      "Compare frames taken at similar wavelengths: dust, detector quality and saturation can imitate a change in brightness.",
    ],
    caution: "A brightness ratio that mixes components, or mixes different wavelengths, has to be labelled as such.",
    refs: ["R02"],
    color: "#ffd166",
  },
  "r-draconis": {
    id: "r-draconis",
    lede: "A pulsating giant that swells and fades over roughly 246 days.",
    body: [
      "R Draconis is a long-period variable. SPHEREx revisits each patch of sky about every six months, which is close to its period, so sampling needs care.",
      "The two original cutouts used in our paper have flagged pixels at the center of the star at both dates.",
    ],
    caution: "Flagged central pixels mean these frames are a quality-control demonstration. They are not a validated brightness measurement.",
    refs: ["R05", "R06", "R17"],
    color: "#6ee7b7",
  },
};

export const GENERAL_REFS = ["R07", "R08", "R09", "R15", "R16"];

export const FIGURES = [
  { file: "fig01_motion_scale.png", title: "How far each moving benchmark travels in half a year, compared with one SPHEREx pixel" },
  { file: "fig03_wise_positions.png", title: "Historical positions of WISE 0855 from published astrometry" },
  { file: "fig04_rw_aur_dimming.png", title: "RW Aurigae A brightness change derived from published flux ratios" },
  { file: "fig05_r_dra_cadence.png", title: "How a 246-day period is sampled by a six-month survey cadence" },
  { file: "fig06_spherex_r_dra.png", title: "Two original SPHEREx cutouts of R Draconis, with quality flags" },
  { file: "fig07_workflow.png", title: "From archive query to a displayed frame" },
];

/** Constellation containing each target, computed with astropy's get_constellation. */
export const CONSTELLATION: Record<string, string> = {
  barnard: "Ophiuchus",
  "epsilon-indi": "Indus",
  "wise-0855": "Hydra",
  "rw-aurigae": "Auriga",
  "r-draconis": "Draco",
};
