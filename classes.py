import json
from pydantic import BaseModel
from typing import List, Dict, Optional

class Bet(BaseModel):
    bet_name: Optional[str] = None
    price: Optional[float] = None
    sportsbooks: Optional[List[str]] = None
    no_vig_price: Optional[float] = None
    edge_percent: Optional[float] = None
    order: Optional[int] = None
    bet_points: Optional[str] = None
    desktop_url: Optional[str] = None

class Arbitrage(BaseModel):
    bet_id: Optional[str] = None
    is_live: Optional[bool] = None
    in_game_status: Optional[str] = None
    percentage: Optional[float] = None
    bets: Optional[List[Bet]] = None