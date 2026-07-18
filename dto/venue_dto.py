from dataclasses import dataclass

@dataclass(frozen=True)  # frozen=Trueでイミュータブル（不変）にする
class VenueDTO:
    name: str
    detail_url: str