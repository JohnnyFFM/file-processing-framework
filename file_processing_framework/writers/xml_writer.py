"""
XML file writer.

Writes DataModel to XML files using xmltodict.
"""

import xmltodict
from datetime import datetime
from typing import Any, Dict, List
from ..core.writer import FileWriter
from ..core.data_model import DataModel
from ..core.exceptions import FileWriteError


class XmlWriter(FileWriter):
    """
    Write DataModel to XML files.

    Uses xmltodict to convert dict structure to XML.

    Supports:
    - Nested structures
    - Attributes (@ prefix)
    - Text content (#text key)
    - Pretty printing
    - Custom root element
    """

    def write(self, data_model: DataModel, filepath: str, config: dict) -> None:
        """
        Write DataModel to XML file.

        Args:
            data_model: Data to write
            filepath: Output file path
            config: Configuration dict with options:
                   - encoding: File encoding (default: utf-8)
                   - pretty: Pretty print with indentation (default: True)
                   - root_element: Root element name if data is list (default: 'root')
                   - item_element: Item element name for list items (default: 'item')
                   - xml_declaration: Include XML declaration (default: True)

        Raises:
            FileWriteError: If file cannot be written

        Note:
            Dict structure conventions for XML:
            - Keys become element names
            - @ prefix for attributes (e.g., {'@id': '1'})
            - #text key for text content
            - Lists become multiple elements with same name

        Example:
            Data:
                {'root': {'record': {'@id': '1', 'name': 'John', 'age': '30'}}}

            XML output:
                <root>
                    <record id="1">
                        <name>John</name>
                        <age>30</age>
                    </record>
                </root>
        """
        self._validate_data_model(data_model)
        self._ensure_output_directory(filepath)

        try:
            # Get configuration
            encoding = config.get('encoding', 'utf-8')
            pretty = config.get('pretty', True)
            root_element = config.get('root_element', 'root')
            item_element = config.get('item_element', 'item')
            xml_declaration = config.get('xml_declaration', True)

            # Prepare data
            data = self._prepare_data(data_model.data, root_element, item_element)

            # Convert to XML
            xml_string = xmltodict.unparse(
                data,
                pretty=pretty,
                encoding=encoding,
                full_document=xml_declaration
            )

            # Write to file
            with open(filepath, 'w', encoding=encoding, errors='replace') as f:
                f.write(xml_string)

        except Exception as e:
            raise FileWriteError(f"Failed to write XML file {filepath}: {e}")

    def _prepare_data(
        self,
        data: Any,
        root_element: str,
        item_element: str
    ) -> Dict[str, Any]:
        """
        Prepare data for XML serialization.

        Args:
            data: Data to prepare
            root_element: Root element name
            item_element: Item element name for lists

        Returns:
            Dict structure suitable for xmltodict
        """
        # Convert datetime and other special types
        data = self._convert_types(data)

        # If data is already a dict with root element, use as-is
        if isinstance(data, dict):
            # Check if dict already has a single root key
            if len(data) == 1:
                return data
            else:
                # Wrap in root element
                return {root_element: data}

        # If data is a list, wrap in root and item elements
        elif isinstance(data, list):
            return {
                root_element: {
                    item_element: data
                }
            }

        # If primitive type, wrap in root with text content
        else:
            return {
                root_element: str(data)
            }

    def _convert_types(self, data: Any) -> Any:
        """
        Recursively convert non-XML-serializable types.

        Args:
            data: Data to convert

        Returns:
            Converted data
        """
        if isinstance(data, datetime):
            return data.isoformat()
        elif isinstance(data, dict):
            return {key: self._convert_types(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_types(item) for item in data]
        elif isinstance(data, bool):
            return str(data).lower()  # 'true' or 'false'
        elif isinstance(data, (str, int, float, type(None))):
            return data
        else:
            return str(data)

    def get_supported_extensions(self) -> list[str]:
        """Get supported file extensions."""
        return ['.xml']
