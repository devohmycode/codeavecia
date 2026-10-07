import { CalculateMetadataFunction, Composition } from "remotion";
import { Montage } from "./Montage";
import type { Props } from "./types";

const parDefaut: Props = {
  fps: 30,
  video: "video.mp4",
  dureeVideo: 1,
  dureeTotale: 1,
  largeurSource: 1920,
  hauteurSource: 1080,
  volumeOriginal: 0,
  voix: [],
  sousTitres: [],
  zooms: [],
  facteurZoom: 1.6,
  curseurX: [],
  musique: null,
  volumeMusique: 0.1,
};

// La durée et la cadence viennent des données du projet.
const metadonnees: CalculateMetadataFunction<Props> = ({ props }) => ({
  fps: props.fps,
  durationInFrames: Math.max(1, Math.ceil(props.dureeTotale * props.fps)),
});

export const RemotionRoot = () => (
  <>
    <Composition
      id="Paysage"
      component={Montage}
      width={1920}
      height={1080}
      fps={30}
      durationInFrames={30}
      defaultProps={parDefaut}
      calculateMetadata={metadonnees}
    />
    <Composition
      id="Vertical"
      component={Montage}
      width={1080}
      height={1920}
      fps={30}
      durationInFrames={30}
      defaultProps={parDefaut}
      calculateMetadata={metadonnees}
    />
  </>
);
