"""
UAW Adapters Package
Модуль адаптеров для Unified Agentic Workspace

Содержит все адаптеры для недоступных сервисов:
- BaseAdapter: Базовый класс адаптеров
- MicrosoftTeamsAdapter: Адаптер для Microsoft Teams
- CalendlyAdapter: Адаптер для Calendly
- VercelAdapter: Адаптер для Vercel
- GammaAdapter: Адаптер для Gamma
- CanvaAdapter: Адаптер для Canva
- ExcalidrawAdapter: Адаптер для Excalidraw
- FigmaAdapter: Адаптер для Figma
- WixAdapter: Адаптер для Wix
"""

from .base import BaseAdapter, AdapterConfig, AdapterResult, AdapterStatus

from .teams_adapter import MicrosoftTeamsAdapter, MicrosoftTeamsConfig
from .calendly_adapter import CalendlyAdapter, CalendlyConfig
from .vercel_adapter import VercelAdapter, VercelConfig
from .gamma_adapter import GammaAdapter, GammaConfig
from .canva_adapter import CanvaAdapter, CanvaConfig
from .excalidraw_adapter import ExcalidrawAdapter, ExcalidrawConfig
from .figma_adapter import FigmaAdapter, FigmaConfig
from .wix_adapter import WixAdapter, WixConfig

# Singleton instances
microsoft_teams_adapter = MicrosoftTeamsAdapter()
calendly_adapter = CalendlyAdapter()
vercel_adapter = VercelAdapter()
gamma_adapter = GammaAdapter()
canva_adapter = CanvaAdapter()
excalidraw_adapter = ExcalidrawAdapter()
figma_adapter = FigmaAdapter()
wix_adapter = WixAdapter()

# All adapters
ADAPTERS = {
    "microsoft_teams": microsoft_teams_adapter,
    "calendly": calendly_adapter,
    "vercel": vercel_adapter,
    "gamma": gamma_adapter,
    "canva": canva_adapter,
    "excalidraw": excalidraw_adapter,
    "figma": figma_adapter,
    "wix": wix_adapter,
}

# Available adapters (for unavailable integrations)
AVAILABLE_ADAPTERS = {
    "microsoft_teams": microsoft_teams_adapter,
    "calendly": calendly_adapter,
    "vercel": vercel_adapter,
    "gamma": gamma_adapter,
    "canva": canva_adapter,
    "excalidraw": excalidraw_adapter,
    "figma": figma_adapter,
    "wix": wix_adapter,
}

__all__ = [
    # Base
    "BaseAdapter",
    "AdapterConfig",
    "AdapterResult",
    "AdapterStatus",
    
    # Config classes
    "MicrosoftTeamsConfig",
    "CalendlyConfig",
    "VercelConfig",
    "GammaConfig",
    "CanvaConfig",
    "ExcalidrawConfig",
    "FigmaConfig",
    "WixConfig",
    
    # Adapter classes
    "MicrosoftTeamsAdapter",
    "CalendlyAdapter",
    "VercelAdapter",
    "GammaAdapter",
    "CanvaAdapter",
    "ExcalidrawAdapter",
    "FigmaAdapter",
    "WixAdapter",
    
    # Singleton instances
    "microsoft_teams_adapter",
    "calendly_adapter",
    "vercel_adapter",
    "gamma_adapter",
    "canva_adapter",
    "excalidraw_adapter",
    "figma_adapter",
    "wix_adapter",
    
    # Collections
    "ADAPTERS",
    "AVAILABLE_ADAPTERS",
]
