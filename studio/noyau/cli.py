"""Point d'entrée : `studio <étape> <projet>` (voir studio/README.md)."""

import argparse
import sys

from .erreurs import ErreurStudio
from .projet import charger, creer


def _etapes(args, p) -> None:
    from pipeline import capture, commentaire, derushage, export, montage, rendu, transcription, voix

    if args.commande in ("capture", "tout") and (args.commande == "capture" or not p.rush.exists()):
        capture.lancer(p, duree=args.duree, force=args.commande == "capture" and args.force)
    if args.commande == "tout" and not p.rush.exists():
        return
    if args.commande in ("transcrire", "tout"):
        transcription.lancer(p, force=args.commande == "transcrire" and args.force)
    if args.commande in ("derusher", "tout"):
        if not derushage.lancer(p, auto=args.auto, force=args.commande == "derusher" and args.force):
            return  # coupes à valider à la main avant de poursuivre
    if args.commande in ("commenter", "tout"):
        commentaire.lancer(p, force=args.commande == "commenter" and args.force, oui=args.oui)
    if args.commande in ("voix", "tout"):
        voix.lancer(p, force=args.commande == "voix" and args.force)
    if args.commande in ("monter", "tout"):
        montage.lancer(p)
    if args.commande in ("rendre", "tout"):
        rendu.lancer(p, formats=[args.format] if getattr(args, "format", None) else None)
    if args.commande in ("exporter", "tout"):
        export.lancer(p)


def _connecteurs() -> None:
    import connecteurs

    for c in connecteurs.tous():
        pret, detail = c.disponible()
        print(f"{'✓' if pret else '✗'} {c.nom:<12} {'local ' if c.local else 'payant'}  {detail}")


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="studio", description="Atelier vidéo local de CodeAvecIA.")
    sous = parser.add_subparsers(dest="commande", required=True, metavar="commande")

    nouveau = sous.add_parser("nouveau", help="créer un projet vidéo")
    nouveau.add_argument("projet")
    nouveau.add_argument("--titre", default="Nouvelle vidéo")

    sous.add_parser("connecteurs", help="état des connecteurs (LM Studio, Claude, VoiceStudio…)")

    aides = {
        "capture": "S1 — enregistrer l'écran",
        "transcrire": "S2 — transcrire la voix de la capture",
        "derusher": "S3 — proposer puis appliquer les coupes",
        "commenter": "S4 — écrire la voix off avec l'IA",
        "voix": "S5 — synthétiser la voix off",
        "monter": "S8 — préparer le montage Remotion",
        "rendre": "S9 — rendre la vidéo (16:9 et 9:16)",
        "exporter": "S11 — écrire la fiche vidéo du site",
        "tout": "enchaîner toutes les étapes (la capture seulement si elle manque)",
    }
    for nom, aide in aides.items():
        commande = sous.add_parser(nom, help=aide)
        commande.add_argument("projet")
        if nom in ("capture", "transcrire", "derusher", "commenter", "voix"):
            commande.add_argument("--force", action="store_true", help="refaire l'étape même si elle est à jour")
        if nom in ("capture", "tout"):
            commande.add_argument("--duree", type=float, help="durée de la capture en secondes")
        if nom in ("derusher", "tout"):
            commande.add_argument("--auto", action="store_true", help="valider les coupes proposées sans relecture")
        if nom in ("commenter", "tout"):
            commande.add_argument("--oui", action="store_true", help="accepter le coût d'un connecteur payant")
        if nom == "rendre":
            commande.add_argument("--format", choices=["paysage", "vertical"])
        commande.set_defaults(auto=False, oui=False, duree=None, force=False)

    args = parser.parse_args(argv)
    try:
        if args.commande == "nouveau":
            print(f"Projet créé : {creer(args.projet, args.titre)}")
        elif args.commande == "connecteurs":
            _connecteurs()
        else:
            _etapes(args, charger(args.projet))
    except ErreurStudio as e:
        print(f"Erreur : {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrompu.", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
