"""Language detection based on YAML mappings."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import yaml


class LanguageDetector:
    """Detects programming languages for files based on configuration.

    This class handles language detection by mapping file extensions and
    specific filenames to programming language names. Language mappings are
    loaded from a YAML configuration file.

    Attributes:
        language_config_path (Path | None): Path to YAML file containing
            language configuration mappings.
        custom_language_mapping (Mapping[str, Any] | None): Optional in-memory
            mapping that overrides or extends YAML language definitions.
        extension_to_lang (dict[str, str]): Maps file extensions to language
            names (e.g., ".py" -> "Python").
        filename_to_lang (dict[str, str]): Maps specific filenames to language
            names (e.g., "Makefile" -> "Make").
    """

    def __init__(
        self,
        language_config_path: Path | None = None,
        custom_language_mapping: Mapping[str, Any] | None = None,
    ) -> None:
        """Initialize the LanguageDetector.

        Args:
            language_config_path (Path | None): Path to a YAML file containing
                language configuration mappings. If provided, the file should
                contain language names as keys with "extensions" and "filenames"
                lists as values. If None or file doesn't exist, all files are
                marked as "unknown" language. Defaults to None.
            custom_language_mapping (Mapping[str, Any] | None): Optional mapping
                that extends or overrides entries in the YAML configuration.
                Custom mappings win on conflicts. Defaults to None.

        Raises:
            ValueError: If language_config_path is provided but contains invalid
                YAML syntax or cannot be read.
        """
        self.language_config_path: Path | None = language_config_path
        self.custom_language_mapping: Mapping[str, Any] | None = custom_language_mapping
        self.extension_to_lang: dict[str, str]
        self.filename_to_lang: dict[str, str]
        self.extension_to_lang, self.filename_to_lang, self.lang_to_category = (
            self._load_language_map()
        )

    def detect(self, file: Path) -> str:
        """Determines the programming language for a given file.

        Checks the file's name first against the filename mappings, then
        its extension against the extension mappings. This ensures that
        files like "Makefile" (without extension) are correctly identified.

        Args:
            file (Path): The file path to identify.

        Returns:
            str: The language name (e.g., "Python", "JavaScript", "Make")
                or "unknown" if no mapping is found.
        """
        if file.name in self.filename_to_lang:
            return self.filename_to_lang[file.name]
        if file.suffix.lower() in self.extension_to_lang:
            return self.extension_to_lang[file.suffix.lower()]
        return "unknown"

    def get_category(self, lang_name: str) -> str:
        """Retrieves the category type for a specific programming language.

        Categories are defined in the language configuration
        (e.g., "programming", "markup", "data") and help group
        related languages together.

        Args:
            lang_name (str): The name of the language to look up.

        Returns:
            str: The category name (e.g., "programming", "markup")
                or "unknown" if the language is not mapped to a category.
        """
        return self.lang_to_category.get(lang_name, "unknown")

    def _load_language_map(
        self,
    ) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
        """Loads and parses the language configuration from a YAML file.

        Reads the YAML file and creates two mappings: one from file extensions
        to language names, and another from specific filenames
        to language names.

        Returns:
                tuple[dict[str, str], dict[str, str], dict[str, str]]: A tuple
                        containing:
                        - extension_to_lang: Maps lowercase extensions (e.g., ".py")
                            to language names (e.g., "Python")
                        - filename_to_lang: Maps exact filenames (e.g., "Makefile")
                            to language names (e.g., "Make")
                        - lang_to_category: Maps language names to category types

        Raises:
            ValueError: If the YAML file exists but contains invalid syntax
                or cannot be read.
        """
        data: dict[str, Any] = self._load_yaml_config()
        merged = self._merge_language_mappings(data, self.custom_language_mapping)
        return self._build_language_mappings(merged)

    def _load_yaml_config(self) -> dict[str, Any]:
        """Loads the language configuration from a YAML file.

        Reads the YAML file if it exists and is valid. If the file doesn't
        exist or no config path is provided, returns an empty dictionary.

        Returns:
            dict[str, Any]: The parsed YAML data as a dictionary.

        Raises:
            ValueError: If the YAML file contains invalid syntax or cannot
                be read.
        """
        if not self.language_config_path or not self.language_config_path.exists():
            return {}

        try:
            with open(self.language_config_path, encoding="utf-8") as f:
                data: Any = yaml.safe_load(f)
                return cast(dict[str, Any], data) if isinstance(data, dict) else {}
        except (yaml.YAMLError, OSError) as e:
            raise ValueError(f"Failed to load language map: {e}") from None

    def _merge_language_mappings(
        self,
        base_data: dict[str, Any],
        custom_mapping: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        """Merge custom mappings into base language data.

        Args:
            base_data: Language mappings loaded from YAML.
            custom_mapping: Custom language mapping from configuration.

        Returns:
            Merged mapping where custom entries override base entries.
        """
        if not custom_mapping:
            return base_data

        merged: dict[str, Any] = dict(base_data)
        for lang_name, custom_info in custom_mapping.items():
            if not isinstance(custom_info, Mapping):
                continue

            base_info = merged.get(lang_name, {})
            if not isinstance(base_info, Mapping):
                base_info = {}

            updated = dict(base_info)
            updated.update(dict(custom_info))
            merged[lang_name] = updated

        return merged

    def _build_language_mappings(
        self, data: dict[str, Any]
    ) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
        """Builds language mappings from parsed YAML configuration.

        Creates two dictionaries: one mapping file extensions to language names,
        and another mapping specific filenames to language names.

        Extensions are normalized to lowercase for case-insensitive matching.

        Args:
            data (dict[str, Any]): The parsed YAML configuration data.

        Returns:
            tuple[dict[str, str], dict[str, str], dict[str, str]]: A tuple
                containing:
                - extension_to_lang: Maps lowercase extensions to language names
                - filename_to_lang: Maps filenames to language names
                - lang_to_category: Maps language names to category types
        """
        extension_to_lang: dict[str, str] = {}
        filename_to_lang: dict[str, str] = {}
        lang_to_category: dict[str, str] = {}

        for lang_name, info in data.items():
            if not isinstance(info, dict):
                continue

            info = cast(dict[str, Any], info)

            self._process_extensions(info, lang_name, extension_to_lang)
            self._process_filenames(info, lang_name, filename_to_lang)
            self._process_category(info, lang_name, lang_to_category)

        return extension_to_lang, filename_to_lang, lang_to_category

    @staticmethod
    def _process_extensions(
        info: dict[str, Any],
        lang_name: str,
        extension_to_lang: dict[str, str],
    ) -> None:
        """Process and map file extensions to language name.

        Args:
            info: Language definition from the YAML configuration.
            lang_name: Name of the language to map extensions for.
            extension_to_lang: Mutable mapping to update with extensions.
        """
        extensions: list[Any] = info.get("extensions", [])
        for ext in extensions:
            if isinstance(ext, str):
                extension_to_lang[ext.lower()] = lang_name

    @staticmethod
    def _process_filenames(
        info: dict[str, Any],
        lang_name: str,
        filename_to_lang: dict[str, str],
    ) -> None:
        """Process and map specific filenames to language name.

        Args:
            info: Language definition from the YAML configuration.
            lang_name: Name of the language to map filenames for.
            filename_to_lang: Mutable mapping to update with filenames.
        """
        filenames: list[Any] = info.get("filenames", [])
        for name in filenames:
            if isinstance(name, str):
                filename_to_lang[name] = lang_name

    @staticmethod
    def _process_category(
        info: dict[str, Any],
        lang_name: str,
        lang_to_category: dict[str, str],
    ) -> None:
        """Process and map language to category type.

        Args:
            info: Language definition from the YAML configuration.
            lang_name: Name of the language to categorize.
            lang_to_category: Mutable mapping to update with category.
        """
        category = info.get("type", "unknown")
        if isinstance(category, str):
            lang_to_category[lang_name] = category
