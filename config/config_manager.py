"""
UAW Configuration Manager
Управление конфигурацией Unified Agentic Workspace
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import logging
import yaml


logger = logging.getLogger(__name__)


class ConfigFormat(Enum):
    """Форматы конфигурации"""
    JSON = "json"
    YAML = "yaml"
    ENV = "env"
    INI = "ini"


@dataclass
class ConfigValue:
    """Значение конфигурации"""
    key: str
    value: Any
    type: str = "string"
    description: str = ""
    required: bool = False
    default: Optional[Any] = None
    sensitive: bool = False
    
    def __post_init__(self):
        if self.value is None and self.default is not None:
            self.value = self.default
            
    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "type": self.type,
            "description": self.description,
            "required": self.required,
            "sensitive": self.sensitive,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfigValue":
        return cls(
            key=data["key"],
            value=data.get("value", data.get("default")),
            type=data.get("type", "string"),
            description=data.get("description", ""),
            required=data.get("required", False),
            default=data.get("default"),
            sensitive=data.get("sensitive", False),
        )


class ConfigManager:
    """
    Менеджер конфигурации
    
    Управляет:
    - Загрузкой конфигурации из файлов
    - Валидацией конфигурации
    - Сохранением конфигурации
    - Работой с переменными окружения
    """
    
    def __init__(
        self,
        config_dir: str = "config",
        env_prefix: str = "UAW_",
    ):
        self.config_dir = Path(config_dir)
        self.env_prefix = env_prefix
        self.config: Dict[str, Any] = {}
        self.config_values: Dict[str, ConfigValue] = {}
        self.loaded_files: List[str] = []
        
        # Создание директории конфигурации
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
    def load_config(
        self,
        config_name: str,
        format: ConfigFormat = ConfigFormat.JSON,
    ) -> bool:
        """
        Загрузка конфигурации из файла
        
        Args:
            config_name: Имя файла конфигурации (без расширения)
            format: Формат файла
            
        Returns:
            bool: True если загрузка успешна
        """
        try:
            if format == ConfigFormat.JSON:
                file_path = self.config_dir / f"{config_name}.json"
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
            elif format == ConfigFormat.YAML:
                file_path = self.config_dir / f"{config_name}.yaml"
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    
            else:
                logger.error(f"Unsupported format: {format}")
                return False
                
            self.config[config_name] = data
            self.loaded_files.append(str(file_path))
            logger.info(f"Loaded config: {file_path}")
            return True
            
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_name}.{format.value}")
            return False
        except Exception as e:
            logger.error(f"Error loading config {config_name}: {e}")
            return False
            
    def load_all_configs(self) -> int:
        """
        Загрузка всех конфигураций из директории
        
        Returns:
            int: Количество загруженных конфигураций
        """
        count = 0
        for config_file in self.config_dir.glob("*.json"):
            if self.load_config(config_file.stem, ConfigFormat.JSON):
                count += 1
                
        for config_file in self.config_dir.glob("*.yaml"):
            if self.load_config(config_file.stem, ConfigFormat.YAML):
                count += 1
                
        return count
        
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Получение значения конфигурации
        
        Args:
            key: Ключ (может быть в формате "section.subsection.key")
            default: Значение по умолчанию
            
        Returns:
            Any: Значение конфигурации или default
        """
        # Проверка в переменных окружения
        env_key = self.env_prefix + key.upper().replace(".", "_").replace("-", "_")
        env_value = os.environ.get(env_key)
        if env_value is not None:
            return self._parse_value(env_value)
            
        # Проверка в загруженной конфигурации
        parts = key.split(".")
        current = self.config
        
        for part in parts:
            if part in current:
                current = current[part]
            else:
                return default
                
        return current if current is not None else default
        
    def get_required(self, key: str) -> Any:
        """
        Получение обязательного значения конфигурации
        
        Args:
            key: Ключ
            
        Returns:
            Any: Значение конфигурации
            
        Raises:
            ValueError: Если значение не найдено
        """
        value = self.get(key)
        if value is None:
            raise ValueError(f"Required config key not found: {key}")
        return value
        
    def set(self, key: str, value: Any, type: str = "string") -> None:
        """
        Установка значения конфигурации
        
        Args:
            key: Ключ
            value: Значение
            type: Тип значения
        """
        # Разбиваем ключ на части
        parts = key.split(".")
        current = self.config
        
        # Создаем вложенные структуры
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
            
        # Устанавливаем значение
        current[parts[-1]] = self._parse_value(value, type)
        
        # Сохраняем ConfigValue
        self.config_values[key] = ConfigValue(
            key=key,
            value=value,
            type=type,
        )
        
    def _parse_value(self, value: Any, type: str = "string") -> Any:
        """Парсинг значения в указанный тип"""
        if value is None:
            return None
            
        if type == "string":
            return str(value)
        elif type == "int":
            return int(value)
        elif type == "float":
            return float(value)
        elif type == "bool":
            if isinstance(value, str):
                return value.lower() in ["true", "1", "yes"]
            return bool(value)
        elif type == "list":
            if isinstance(value, str):
                return value.split(",")
            return list(value)
        elif type == "dict":
            if isinstance(value, str):
                return json.loads(value)
            return dict(value)
        else:
            return value
            
    def save_config(
        self,
        config_name: str,
        data: Dict[str, Any],
        format: ConfigFormat = ConfigFormat.JSON,
    ) -> bool:
        """
        Сохранение конфигурации в файл
        
        Args:
            config_name: Имя файла конфигурации
            data: Данные для сохранения
            format: Формат файла
            
        Returns:
            bool: True если сохранение успешно
        """
        try:
            if format == ConfigFormat.JSON:
                file_path = self.config_dir / f"{config_name}.json"
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    
            elif format == ConfigFormat.YAML:
                file_path = self.config_dir / f"{config_name}.yaml"
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, allow_unicode=True)
                    
            else:
                logger.error(f"Unsupported format: {format}")
                return False
                
            logger.info(f"Saved config: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving config {config_name}: {e}")
            return False
            
    def validate_config(
        self,
        config_name: str,
        schema: Dict[str, Any],
    ) -> Tuple[bool, List[str]]:
        """
        Валидация конфигурации по схеме
        
        Args:
            config_name: Имя конфигурации
            schema: Схема валидации
            
        Returns:
            Tuple[bool, List[str]]: (успех, список ошибок)
        """
        errors = []
        config = self.config.get(config_name, {})
        
        for field, field_schema in schema.items():
            required = field_schema.get("required", False)
            value = config.get(field)
            
            if required and value is None:
                errors.append(f"Missing required field: {field}")
                continue
                
            if value is not None:
                field_type = field_schema.get("type", "string")
                if field_type == "string" and not isinstance(value, str):
                    errors.append(f"Field {field} must be string")
                elif field_type == "int" and not isinstance(value, int):
                    errors.append(f"Field {field} must be int")
                elif field_type == "bool" and not isinstance(value, bool):
                    errors.append(f"Field {field} must be bool")
                elif field_type == "list" and not isinstance(value, list):
                    errors.append(f"Field {field} must be list")
                elif field_type == "dict" and not isinstance(value, dict):
                    errors.append(f"Field {field} must be dict")
                    
        return len(errors) == 0, errors
        
    def get_config_value(self, key: str) -> Optional[ConfigValue]:
        """Получение ConfigValue по ключу"""
        return self.config_values.get(key)
        
    def list_configs(self) -> List[str]:
        """Получение списка загруженных конфигураций"""
        return list(self.config.keys())
        
    def reload_config(self, config_name: str) -> bool:
        """Перезагрузка конфигурации"""
        if config_name in self.config:
            del self.config[config_name]
            
        # Удаляем соответствующие ConfigValue
        to_remove = [k for k in self.config_values if k.startswith(config_name)]
        for key in to_remove:
            del self.config_values[key]
            
        return self.load_config(config_name)
        
    def reset(self) -> None:
        """Сброс всех конфигураций"""
        self.config.clear()
        self.config_values.clear()
        self.loaded_files.clear()
        logger.info("Config manager reset")
