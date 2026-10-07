// Données produites par `studio monter` (studio/pipeline/montage.py) dans media/<projet>/props.json.
// Les temps sont en secondes ; les fichiers sont relatifs au dossier public media/<projet>/public/.

export type Clip = { fichier: string; debut: number; duree: number };
export type SousTitre = { debut: number; fin: number; texte: string };
// x et y : point visé, en fraction de la largeur et de la hauteur de la capture.
export type Zoom = { debut: number; fin: number; x: number; y: number };

export type Props = {
  fps: number;
  video: string;
  dureeVideo: number;
  dureeTotale: number;
  largeurSource: number;
  hauteurSource: number;
  volumeOriginal: number;
  voix: Clip[];
  sousTitres: SousTitre[];
  zooms: Zoom[];
  facteurZoom: number;
  // Position horizontale lissée du curseur (0–1), une valeur par image : cadrage du format vertical.
  curseurX: number[];
  musique: string | null;
  volumeMusique: number;
};
