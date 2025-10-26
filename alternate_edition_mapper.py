#!/usr/bin/env python3
"""
Intelligent Alternate Edition Volume Mapper
Handles mapping between alternate edition formats and standard volume ranges
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class VolumeMapping:
    """Represents a mapping between alternate edition and standard volumes"""
    alternate_edition_name: str
    standard_series_name: str
    mapping_rules: Dict[str, str]  # alternate_volume -> standard_volume_range
    volumes_per_book: Optional[int] = None
    description: str = ""


class AlternateEditionMapper:
    """Maps alternate edition volumes to standard volume ranges"""

    def __init__(self):
        # Pre-defined mappings for known alternate editions
        self.mappings = {
            "Attack on Titan: Colossal Edition": VolumeMapping(
                alternate_edition_name="Attack on Titan: Colossal Edition",
                standard_series_name="Attack on Titan",
                volumes_per_book=5,
                description="Each Colossal Edition contains 5 standard volumes",
                mapping_rules=self._generate_colossal_mapping(34)
            ),
            "Attack on Titan: No Regrets": VolumeMapping(
                alternate_edition_name="Attack on Titan: No Regrets",
                standard_series_name="Attack on Titan",
                description="Prequel series - standalone volumes",
                mapping_rules={"1": "1", "2": "2"}
            ),
            "Attack on Titan: Before the Fall": VolumeMapping(
                alternate_edition_name="Attack on Titan: Before the Fall",
                standard_series_name="Attack on Titan",
                description="Prequel series - standalone volumes",
                mapping_rules={"1": "1", "2": "2", "3": "3"}
            ),
            "Boruto: Two Blue Vortex": VolumeMapping(
                alternate_edition_name="Boruto: Two Blue Vortex",
                standard_series_name="Boruto: Naruto Next Generation",
                description="Continuation of Boruto series",
                mapping_rules=self._generate_sequential_mapping("Boruto: Two Blue Vortex", 2)
            ),
            "My Hero Academia": VolumeMapping(
                alternate_edition_name="My Hero Academia",
                standard_series_name="My Hero Academia",
                description="Standard series - ongoing",
                mapping_rules=self._generate_sequential_mapping("My Hero Academia", 41)
            ),
            "To Your Eternity": VolumeMapping(
                alternate_edition_name="To Your Eternity",
                standard_series_name="To Your Eternity",
                description="Standard series - ongoing",
                mapping_rules=self._generate_sequential_mapping("To Your Eternity", 22)
            ),
            "Spy x Family": VolumeMapping(
                alternate_edition_name="Spy x Family",
                standard_series_name="Spy x Family",
                description="Standard series - 1 volume per book",
                mapping_rules=self._generate_sequential_mapping("Spy x Family", 13)
            ),
            "Magus of the Library": VolumeMapping(
                alternate_edition_name="Magus of the Library",
                standard_series_name="Magus of the Library",
                description="Standard series - 1 volume per book",
                mapping_rules=self._generate_sequential_mapping("Magus of the Library", 8)
            ),
            "Crayon Shinchan": VolumeMapping(
                alternate_edition_name="Crayon Shinchan",
                standard_series_name="Crayon Shinchan",
                description="Omnibus edition - 10 volumes per book",
                volumes_per_book=10,
                mapping_rules=self._generate_colossal_mapping(50)
            ),
            "Sho-ha Shoten": VolumeMapping(
                alternate_edition_name="Sho-ha Shoten",
                standard_series_name="Sho-ha Shoten",
                description="Standard series - 11 volumes",
                mapping_rules=self._generate_sequential_mapping("Sho-ha Shoten", 11)
            ),
            "Otherworldly Izakaya Nobu": VolumeMapping(
                alternate_edition_name="Otherworldly Izakaya Nobu",
                standard_series_name="Otherworldly Izakaya Nobu",
                description="20 manga volumes, 7 light novel volumes",
                mapping_rules=self._generate_sequential_mapping("Otherworldly Izakaya Nobu", 20)
            ),
            "Blue Note": VolumeMapping(
                alternate_edition_name="Blue Note",
                standard_series_name="Blue Giant",
                description="Blue Giant series - 10 manga volumes, omnibus edition exists",
                mapping_rules=self._generate_sequential_mapping("Blue Giant", 10)
            )
        }

    def _generate_colossal_mapping(self, total_standard_volumes: int) -> Dict[str, str]:
        """Generate mapping for Colossal Edition format (5 volumes per book)"""
        mapping = {}
        colossal_books = (total_standard_volumes + 4) // 5  # Ceiling division

        for book_num in range(1, colossal_books + 1):
            start_vol = (book_num - 1) * 5 + 1
            end_vol = min(book_num * 5, total_standard_volumes)
            mapping[str(book_num)] = f"{start_vol}-{end_vol}"

        return mapping

    def _generate_sequential_mapping(self, series_name: str, total_volumes: int) -> Dict[str, str]:
        """Generate 1:1 mapping for standard sequential volumes"""
        return {str(i): str(i) for i in range(1, total_volumes + 1)}

    def get_volume_range(self, series_name: str, alternate_volume: str) -> Optional[str]:
        """Get the standard volume range for an alternate edition volume"""
        if series_name not in self.mappings:
            return None

        mapping = self.mappings[series_name]
        return mapping.mapping_rules.get(str(alternate_volume))

    def get_total_volumes(self, series_name: str) -> Optional[int]:
        """Get total number of volumes for a series"""
        if series_name in self.mappings:
            mapping = self.mappings[series_name]
            return len(mapping.mapping_rules)
        return None

    def is_alternate_edition(self, series_name: str) -> bool:
        """Check if a series is an alternate edition"""
        return series_name in self.mappings

    def get_standard_series_name(self, alternate_edition_name: str) -> Optional[str]:
        """Get the standard series name for an alternate edition"""
        if alternate_edition_name in self.mappings:
            return self.mappings[alternate_edition_name].standard_series_name
        return None

    def parse_volume_description(self, description: str) -> Dict[str, any]:
        """Parse volume descriptions to extract volume ranges"""
        result = {
            'volume_range': None,
            'total_volumes': None,
            'is_alternate_edition': False,
            'description': description
        }

        # Pattern for "X (in the Colossal Edition format, which collects...)"
        colossal_pattern = r'(\d+)\s*\(in the Colossal Edition format'
        match = re.search(colossal_pattern, description)
        if match:
            book_num = int(match.group(1))
            result['is_alternate_edition'] = True
            result['volume_range'] = self.get_volume_range("Attack on Titan: Colossal Edition", book_num)
            result['total_volumes'] = 7  # Total Colossal Edition books
            return result

        # Pattern for "X (as of Y)"
        as_of_pattern = r'(\d+)\s*\(as of'
        match = re.search(as_of_pattern, description)
        if match:
            volume_count = int(match.group(1))
            result['volume_range'] = f"1-{volume_count}"
            result['total_volumes'] = volume_count
            return result

        # Pattern for simple volume numbers
        simple_pattern = r'^(\d+)$'
        match = re.search(simple_pattern, description)
        if match:
            volume_count = int(match.group(1))
            result['volume_range'] = f"1-{volume_count}"
            result['total_volumes'] = volume_count
            return result

        return result

    def get_volume_info_for_series(self, series_name: str) -> Dict[str, any]:
        """Get comprehensive volume information for a series"""
        if series_name in self.mappings:
            mapping = self.mappings[series_name]
            return {
                'series_name': series_name,
                'is_alternate_edition': True,
                'standard_series_name': mapping.standard_series_name,
                'total_volumes': len(mapping.mapping_rules),
                'volumes_per_book': mapping.volumes_per_book,
                'description': mapping.description,
                'volume_mapping': mapping.mapping_rules
            }
        else:
            # Assume it's a standard series
            return {
                'series_name': series_name,
                'is_alternate_edition': False,
                'standard_series_name': series_name,
                'total_volumes': None,  # Will be determined from API
                'volumes_per_book': 1,
                'description': 'Standard manga series',
                'volume_mapping': {}
            }


def main():
    """Test the alternate edition mapper"""
    mapper = AlternateEditionMapper()

    # Test cases
    test_cases = [
        "Attack on Titan: Colossal Edition",
        "Boruto: Two Blue Vortex",
        "My Hero Academia",
        "To Your Eternity",
        "One Piece"  # Standard series
    ]

    print("🧪 Testing Alternate Edition Mapper")
    print("=" * 50)

    for series in test_cases:
        info = mapper.get_volume_info_for_series(series)
        print(f"\n📚 {series}")
        print(f"   Alternate Edition: {info['is_alternate_edition']}")
        print(f"   Standard Series: {info['standard_series_name']}")
        print(f"   Total Volumes: {info['total_volumes']}")
        print(f"   Description: {info['description']}")

        if info['is_alternate_edition'] and info['volume_mapping']:
            print(f"   Sample Mapping: {dict(list(info['volume_mapping'].items())[:3])}...")


if __name__ == "__main__":
    main()