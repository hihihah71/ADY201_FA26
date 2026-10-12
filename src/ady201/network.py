from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RoadNetworkFiles:
    nodes: Path
    edges: Path
