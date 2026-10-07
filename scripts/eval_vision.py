"""Run local photo checks on a folder and print a compact results table."""
from __future__ import annotations
import argparse
from pathlib import Path
from grassquest.images import prepare_image
from grassquest.llm import DEFAULT_MODEL, check_photo

def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder",type=Path)
    parser.add_argument("--task",default=None)
    parser.add_argument("--model",default=DEFAULT_MODEL)
    args=parser.parse_args()
    files=sorted(p for p in args.folder.iterdir() if p.suffix.lower() in {".jpg",".jpeg",".png",".webp"})
    print(f"{'FILE':36} {'MATCH':8} {'CONFIDENCE':10} DESCRIPTION")
    print("-"*110)
    for file in files:
        try:
            content,_=prepare_image(file.read_bytes())
            result=check_photo(content,args.task,args.model)
            print(f"{file.name[:35]:36} {result.match:8} {result.confidence:10} {result.description}")
        except Exception as exc:
            print(f"{file.name[:35]:36} ERROR    -          {exc}")

if __name__=="__main__": main()
