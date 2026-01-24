"""
Custom parsers for handling nested FormData with bracket notation.
"""

from rest_framework.parsers import MultiPartParser as DRFMultiPartParser
from rest_framework.parsers import DataAndFiles


class NestedMultiPartParser(DRFMultiPartParser):
    """
    Parser for multipart form data with nested bracket notation support.

    Converts keys like:
    - attachments[0][file] -> {"attachments": [{"file": ...}]}
    - production_items[1][id] -> {"production_items": [{}, {"id": ...}]}

    Usage:
        parser_classes = (NestedMultiPartParser, JSONParser, FormParser)
    """

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Parse the incoming bytestream and return parsed data with files.
        """
        result = super().parse(stream, media_type, parser_context)

        # Merge files into data (files are stored separately by DRF's MultiPartParser)
        # We need to merge them before processing nested structure
        merged_data = dict(result.data)
        for key, value in result.files.items():
            merged_data[key] = value

        # Convert flat bracket notation to nested structure
        data = self._parse_nested_data(merged_data)

        # Return with empty files dict since we've merged everything into data
        return DataAndFiles(data, {})

    def _parse_nested_data(self, data):
        """
        Convert bracket notation keys to nested dictionaries.

        Example:
            Input: {"items[0][name]": "foo", "items[0][id]": "1", "items[1][name]": "bar"}
            Output: {"items": [{"name": "foo", "id": "1"}, {"name": "bar"}]}
        """
        result = {}

        for key, value in data.items():
            # QueryDict returns lists for all values, even single values
            # Unwrap single-item lists
            if isinstance(value, list) and len(value) == 1:
                value = value[0]

            self._set_nested_value(result, key, value)

        return result

    def _set_nested_value(self, obj, key, value):
        """
        Set a value in a nested structure using bracket notation key.

        Handles keys like:
        - "name" -> obj["name"] = value
        - "items[0]" -> obj["items"][0] = value
        - "items[0][name]" -> obj["items"][0]["name"] = value
        """
        # Parse the key to extract parts
        parts = self._parse_key(key)

        # Navigate to the target location
        current = obj
        for i, part in enumerate(parts[:-1]):
            key_name, index = part

            if index is not None:
                # Array access: items[0]
                if key_name not in current:
                    current[key_name] = []

                # Ensure the array is large enough
                while len(current[key_name]) <= index:
                    current[key_name].append({})

                current = current[key_name][index]
            else:
                # Object access: nested.key
                if key_name not in current:
                    current[key_name] = {}

                current = current[key_name]

        # Set the final value
        final_key, final_index = parts[-1]

        if final_index is not None:
            # Array element
            if final_key not in current:
                current[final_key] = []

            while len(current[final_key]) <= final_index:
                current[final_key].append(None)

            current[final_key][final_index] = value
        else:
            # Direct key
            current[final_key] = value

    def _parse_key(self, key):
        """
        Parse a bracket notation key into parts.

        Examples:
            "name" -> [("name", None)]
            "items[0]" -> [("items", 0)]
            "items[0][name]" -> [("items", 0), ("name", None)]
            "items[1][sub][0]" -> [("items", 1), ("sub", None), (None, 0)]

        Returns list of tuples: [(key_name, index), ...]
        where index is None for non-array access
        """
        parts = []
        current_key = ""
        i = 0

        while i < len(key):
            char = key[i]

            if char == "[":
                # Save current key if any
                if current_key:
                    parts.append((current_key, None))
                    current_key = ""

                # Find matching ]
                j = i + 1
                while j < len(key) and key[j] != "]":
                    j += 1

                # Extract the bracket content
                bracket_content = key[i + 1:j]

                # Check if it's a number (array index)
                if bracket_content.isdigit():
                    # If there's no previous key, this is a continuation
                    # e.g., items[0][1] where [1] is a nested array
                    if parts and parts[-1][1] is None:
                        # Last part was a key without index, assign index to it
                        last_key, _ = parts.pop()
                        parts.append((last_key, int(bracket_content)))
                    else:
                        # Standalone array index (shouldn't happen normally)
                        parts.append((None, int(bracket_content)))
                else:
                    # It's a key inside brackets: items[name]
                    parts.append((bracket_content, None))

                i = j + 1
            else:
                current_key += char
                i += 1

        # Add remaining key if any
        if current_key:
            parts.append((current_key, None))

        return parts if parts else [("", None)]
