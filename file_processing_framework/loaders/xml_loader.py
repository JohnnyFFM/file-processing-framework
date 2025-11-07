"""
XML file loader.

Loads XML files and converts them to DataModel using xmltodict.
"""

import xmltodict
from pathlib import Path
from typing import Dict, Any
from ..core.loader import FileLoader
from ..core.data_model import DataModel
from ..core.exceptions import FileLoadError
from ..formats.detector import FormatDetector


class XmlLoader(FileLoader):
    """
    Load XML files into DataModel.

    Uses xmltodict to convert XML to nested dict structure.

    Supports:
    - Auto-detection of encoding
    - Nested elements
    - Attributes (prefixed with @)
    - Text content (#text key)
    - Root element extraction
    """

    def __init__(self):
        """Initialize XML loader."""
        self.detector = FormatDetector()

    def load(self, filepath: str, config: dict) -> DataModel:
        """
        Load XML file and return DataModel.

        Args:
            filepath: Path to XML file
            config: Configuration dict with options:
                   - encoding: File encoding (auto-detect if not provided)
                   - root_element: Optional root element to extract (e.g., "records")
                   - force_list: Optional list of elements to always parse as lists

        Returns:
            DataModel: Loaded data as nested dict

        Raises:
            FileLoadError: If file cannot be loaded or parsed

        Note:
            XML is converted to dict with these conventions:
            - Elements become dict keys
            - Attributes are prefixed with @ (e.g., @id, @name)
            - Text content is stored in #text key
            - Multiple elements with same name become lists

        Example:
            XML:
                <root>
                    <record id="1">
                        <name>John</name>
                        <age>30</age>
                    </record>
                </root>

            Converts to:
                {
                    'root': {
                        'record': {
                            '@id': '1',
                            'name': 'John',
                            'age': '30'
                        }
                    }
                }
        """
        self._validate_file_exists(filepath)

        try:
            # Get or detect encoding
            encoding = config.get('encoding')
            if not encoding:
                encoding_info = self.detector.detect_encoding(filepath)
                encoding = encoding_info['encoding']

            # Read XML file
            with open(filepath, 'r', encoding=encoding, errors='replace') as f:
                xml_content = f.read()

            # Parse XML to dict
            force_list = config.get('force_list')
            if force_list:
                data = xmltodict.parse(
                    xml_content,
                    force_list=force_list
                )
            else:
                data = xmltodict.parse(xml_content)

            # Extract specific root element if specified
            root_element = config.get('root_element')
            if root_element:
                data = self._extract_element(data, root_element)

            # Create metadata
            metadata = self._get_file_metadata(filepath, 'xml')
            metadata.update({
                'encoding': encoding,
                'data_type': type(data).__name__,
                'root_element': root_element or list(data.keys())[0] if isinstance(data, dict) else None
            })

            return DataModel(data, metadata)

        except Exception as e:
            raise FileLoadError(f"Failed to load XML file {filepath}: {e}")

    def _extract_element(self, data: Dict[str, Any], element_path: str) -> Any:
        """
        Extract specific element from XML dict.

        Args:
            data: Parsed XML dict
            element_path: Dot-separated path to element (e.g., "root.records")

        Returns:
            Extracted element data

        Raises:
            FileLoadError: If element not found
        """
        keys = element_path.split('.')
        current = data

        try:
            for key in keys:
                if isinstance(current, dict):
                    current = current[key]
                else:
                    raise FileLoadError(f"Cannot navigate path '{element_path}' in XML data")

            return current

        except KeyError as e:
            raise FileLoadError(f"Element '{element_path}' not found in XML data: {e}")

    def get_supported_extensions(self) -> list[str]:
        """Get supported file extensions."""
        return ['.xml']
