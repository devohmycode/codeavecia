import { Audio, Video } from "@remotion/media";
import {
  AbsoluteFill,
  Easing,
  Freeze,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { Props, Zoom } from "./types";

const TRANSITION_ZOOM = 0.45; // secondes pour entrer dans un zoom et pour en sortir

// Facteur d'agrandissement à l'instant t (1 hors des zooms), et point visé.
const zoomA = (t: number, zooms: Zoom[], facteur: number) => {
  const z = zooms.find((z) => t >= z.debut && t <= z.fin);
  if (!z) return { echelle: 1, x: 0.5, y: 0.5 };
  const progression = interpolate(
    t,
    [z.debut, z.debut + TRANSITION_ZOOM, z.fin - TRANSITION_ZOOM, z.fin],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) },
  );
  return { echelle: 1 + (facteur - 1) * progression, x: z.x, y: z.y };
};

export const Montage: React.FC<Props> = (p) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const vertical = height > width;
  const t = frame / fps;
  const imagesVideo = Math.max(1, Math.floor(p.dureeVideo * fps));

  // Paysage : la capture tient dans le cadre. Vertical : elle remplit la hauteur et suit le curseur.
  let echelle = vertical ? height / p.hauteurSource : Math.min(width / p.largeurSource, height / p.hauteurSource);
  const largeur = p.largeurSource * echelle;
  const hauteurVideo = p.hauteurSource * echelle;
  let gauche = (width - largeur) / 2;
  if (vertical && largeur > width) {
    const cx = p.curseurX.length ? p.curseurX[Math.min(frame, p.curseurX.length - 1)] : 0.5;
    gauche = Math.min(0, Math.max(width - largeur, width / 2 - cx * largeur));
  }
  const haut = (height - hauteurVideo) / 2;
  const zoom = vertical ? { echelle: 1, x: 0.5, y: 0.5 } : zoomA(t, p.zooms, p.facteurZoom);
  echelle = zoom.echelle;

  const video = (volume: number) => (
    <Video
      src={staticFile(p.video)}
      volume={volume}
      muted={volume === 0}
      style={{ width: largeur, height: hauteurVideo }}
    />
  );
  const sousTitre = p.sousTitres.find((s) => t >= s.debut && t < s.fin);

  return (
    <AbsoluteFill style={{ backgroundColor: "#0b0d0c" }}>
      <div
        style={{
          position: "absolute",
          left: gauche,
          top: haut,
          width: largeur,
          height: hauteurVideo,
          transform: `scale(${echelle})`,
          transformOrigin: `${zoom.x * 100}% ${zoom.y * 100}%`,
        }}
      >
        <Sequence durationInFrames={imagesVideo}>{video(p.volumeOriginal)}</Sequence>
        {/* Si la voix off dépasse la capture, la dernière image reste affichée. */}
        <Sequence from={imagesVideo}>
          <Freeze frame={imagesVideo - 1}>{video(0)}</Freeze>
        </Sequence>
      </div>

      {p.voix.map((clip) => (
        <Sequence
          key={clip.fichier + clip.debut}
          from={Math.round(clip.debut * fps)}
          durationInFrames={Math.ceil(clip.duree * fps) + 1}
          layout="none"
        >
          <Audio src={staticFile(clip.fichier)} />
        </Sequence>
      ))}
      {p.musique ? <Audio src={staticFile(p.musique)} volume={p.volumeMusique} loop /> : null}

      {sousTitre ? (
        <div
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            bottom: vertical ? height * 0.18 : 64,
            display: "flex",
            justifyContent: "center",
            padding: "0 48px",
          }}
        >
          <span
            style={{
              maxWidth: vertical ? 960 : 1480,
              padding: "12px 24px",
              borderRadius: 14,
              backgroundColor: "rgba(11, 13, 12, 0.78)",
              color: "#f4f3ee",
              fontFamily: "'Segoe UI', system-ui, sans-serif",
              fontSize: vertical ? 54 : 42,
              fontWeight: 600,
              lineHeight: 1.3,
              textAlign: "center",
            }}
          >
            {sousTitre.texte}
          </span>
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
